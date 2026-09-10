"""
Crawler — PRD Sections 6.1.3, 6.1.4, and rendered branding support.

Features:
  - robots.txt and sitemap discovery
  - BFS internal-link extraction
  - HTTPX fast-path + Playwright SPA fallback
  - SSRF validation on URLs and browser requests
  - concurrency control
  - dedicated Playwright-based rendered branding extraction
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import re
from collections import deque
from dataclasses import dataclass
from typing import Any, List, Optional
from urllib.parse import urljoin
from urllib.robotparser import RobotFileParser

import httpx
from bs4 import BeautifulSoup

from app.core.config import Settings
from app.services.extractor import extract_page_content
from app.services.ssrf_guard import validate_url
from app.services.url_normalizer import (
    extract_origin,
    is_asset_url,
    is_same_origin,
    normalize_url,
)

logger = logging.getLogger(__name__)

_USER_AGENT = "EmbedIQ-Crawler/2.0 (+https://embediq.io/bot)"

_SPA_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r'<div[^>]+id=["\']root["\'][^>]*>\s*</div>', re.IGNORECASE),
    re.compile(r'<div[^>]+id=["\']__next["\'][^>]*>\s*</div>', re.IGNORECASE),
    re.compile(r'<app-root[^>]*>\s*</app-root>', re.IGNORECASE),
    re.compile(r'<div[^>]+id=["\']app["\'][^>]*>\s*</div>', re.IGNORECASE),
)

_SPA_META: re.Pattern[str] = re.compile(
    r'<meta[^>]+(?:name=["\']next-head-count["\']|name=["\']generator["\'][^>]*'
    r'(?:react|vue|angular|next\.js|nuxt|svelte))',
    re.IGNORECASE,
)

_MIN_TEXT_LENGTH = 200


@dataclass
class CrawlResult:
    url: str
    canonical_url: Optional[str]
    title: str
    http_status: int
    content_type: str
    raw_html: str
    clean_text: str
    structured_data: dict
    content_hash: str
    crawl_status: str
    render_mode: str
    error_code: Optional[str] = None
    error_message: Optional[str] = None


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def _is_spa(html: str, clean_text: str) -> bool:
    if len(clean_text) < _MIN_TEXT_LENGTH:
        for pattern in _SPA_PATTERNS:
            if pattern.search(html):
                return True
        return True

    if _SPA_META.search(html):
        return True

    return False


def _extract_canonical(soup: BeautifulSoup, base_url: str) -> Optional[str]:
    link = soup.find("link", rel=lambda r: r and "canonical" in r)
    if link and link.get("href"):
        try:
            return normalize_url(str(link["href"]), base_url)
        except Exception:
            pass
    return None


def _extract_links(soup: BeautifulSoup, base_url: str, origin: str) -> list[str]:
    seen: set[str] = set()
    links: list[str] = []

    for tag in soup.find_all("a", href=True):
        href = str(tag["href"]).strip()

        if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue

        try:
            abs_url = urljoin(base_url, href)
            norm = normalize_url(abs_url, base_url)
        except Exception:
            continue

        if is_asset_url(norm):
            continue

        if not is_same_origin(norm, origin):
            continue

        if norm in seen:
            continue

        try:
            validate_url(norm)
        except ValueError:
            continue

        seen.add(norm)
        links.append(norm)

    return links


def _build_failed_result(
    url: str,
    http_status: int,
    error_code: str,
    error_message: str,
    render_mode: str = "HTTP",
) -> CrawlResult:
    return CrawlResult(
        url=url,
        canonical_url=None,
        title="",
        http_status=http_status,
        content_type="",
        raw_html="",
        clean_text="",
        structured_data={},
        content_hash="",
        crawl_status="FAILED",
        render_mode=render_mode,
        error_code=error_code,
        error_message=error_message,
    )


class Crawler:
    def __init__(self, origin: str, settings: Settings) -> None:
        self.origin = extract_origin(origin)
        self.settings = settings
        self._http_headers = {"User-Agent": _USER_AGENT}

    # ------------------------------------------------------------------
    # Browser SSRF protection
    # ------------------------------------------------------------------

    async def _install_browser_ssrf_guard(self, context: Any) -> None:
        """Validate browser network requests before Chromium sends them.

        http/https requests are checked by the same SSRF guard used elsewhere.
        Harmless browser-local schemes needed by modern pages are allowed.
        """

        async def route_handler(route: Any, request: Any) -> None:
            request_url = request.url
            scheme = request_url.split(":", 1)[0].lower() if ":" in request_url else ""

            if scheme in {"http", "https"}:
                try:
                    validate_url(request_url)
                except ValueError as exc:
                    logger.warning(
                        "Blocked Playwright request by SSRF policy: %s (%s)",
                        request_url,
                        exc,
                    )
                    await route.abort("blockedbyclient")
                    return

            elif scheme not in {"data", "blob", "about"}:
                logger.debug("Blocked unsupported browser URL scheme: %s", request_url)
                await route.abort("blockedbyclient")
                return

            await route.continue_()

        await context.route("**/*", route_handler)

    # ------------------------------------------------------------------
    # robots.txt
    # ------------------------------------------------------------------

    async def _fetch_robots(self, client: httpx.AsyncClient) -> RobotFileParser:
        rp = RobotFileParser()
        robots_url = f"{self.origin}/robots.txt"

        try:
            validate_url(robots_url)
            resp = await client.get(robots_url, follow_redirects=True)
            if resp.status_code == 200:
                rp.parse(resp.text.splitlines())
        except Exception as exc:
            logger.debug("Could not fetch robots.txt for %s: %s", self.origin, exc)

        return rp

    def _is_allowed(self, rp: RobotFileParser, url: str) -> bool:
        try:
            return rp.can_fetch(_USER_AGENT, url)
        except Exception:
            return True

    # ------------------------------------------------------------------
    # Sitemap discovery
    # ------------------------------------------------------------------

    async def _fetch_sitemap_urls(
        self,
        client: httpx.AsyncClient,
        sitemap_url: str,
        depth: int = 0,
    ) -> list[str]:
        if depth > 3:
            return []

        urls: list[str] = []

        try:
            validate_url(sitemap_url)
            resp = await client.get(sitemap_url, follow_redirects=True)

            if resp.status_code != 200:
                return []

            soup = BeautifulSoup(resp.text, "lxml-xml")

            for sitemap_tag in soup.find_all("sitemap"):
                loc = sitemap_tag.find("loc")
                if loc and loc.get_text(strip=True):
                    child_urls = await self._fetch_sitemap_urls(
                        client,
                        loc.get_text(strip=True),
                        depth + 1,
                    )
                    urls.extend(child_urls)

            for url_tag in soup.find_all("url"):
                loc = url_tag.find("loc")
                if loc and loc.get_text(strip=True):
                    page_url = loc.get_text(strip=True)
                    try:
                        norm = normalize_url(page_url)
                        if is_same_origin(norm, self.origin) and not is_asset_url(norm):
                            urls.append(norm)
                    except Exception:
                        continue

        except Exception as exc:
            logger.debug("Sitemap fetch failed for %s: %s", sitemap_url, exc)

        return urls

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    async def discover_pages(self, seed_url: str) -> list[str]:
        try:
            seed_url = validate_url(normalize_url(seed_url))
        except ValueError as exc:
            logger.error("Seed URL failed SSRF validation: %s", exc)
            return []

        max_pages = self.settings.MAX_PAGES_PER_BOT
        max_depth = self.settings.MAX_CRAWL_DEPTH
        timeout = httpx.Timeout(self.settings.HTTP_TIMEOUT_SECONDS)

        discovered: set[str] = {seed_url}
        queue: deque[tuple[str, int]] = deque([(seed_url, 0)])

        async with httpx.AsyncClient(
            headers=self._http_headers,
            timeout=timeout,
            follow_redirects=False,
            max_redirects=0,
        ) as client:
            rp = await self._fetch_robots(client)

            sitemap_urls_from_robots: list[str] = []
            site_maps = rp.site_maps()

            if site_maps:
                sitemap_urls_from_robots = list(site_maps)

            default_sitemap = f"{self.origin}/sitemap.xml"

            if default_sitemap not in sitemap_urls_from_robots:
                sitemap_urls_from_robots.insert(0, default_sitemap)

            for sitemap_url in sitemap_urls_from_robots:
                sm_urls = await self._fetch_sitemap_urls(client, sitemap_url)

                for item in sm_urls:
                    if item not in discovered and self._is_allowed(rp, item):
                        discovered.add(item)
                        queue.append((item, 1))

                    if len(discovered) >= max_pages:
                        break

                if len(discovered) >= max_pages:
                    break

            while queue and len(discovered) < max_pages:
                current_url, depth = queue.popleft()

                if depth >= max_depth:
                    continue

                try:
                    validate_url(current_url)
                    resp = await client.get(current_url)

                    hops = 0
                    while resp.is_redirect and hops < self.settings.MAX_REDIRECTS:
                        redirect_location = resp.headers.get("location", "")
                        abs_redirect = urljoin(current_url, redirect_location)

                        try:
                            validate_url(abs_redirect)
                        except ValueError:
                            break

                        resp = await client.get(abs_redirect)
                        current_url = abs_redirect
                        hops += 1

                    if resp.status_code != 200:
                        continue

                    content_type = resp.headers.get("content-type", "")
                    if (
                        "text/html" not in content_type
                        and "application/xhtml" not in content_type
                    ):
                        continue

                    soup = BeautifulSoup(resp.text, "html.parser")
                    links = _extract_links(soup, current_url, self.origin)

                    for link in links:
                        if link not in discovered and self._is_allowed(rp, link):
                            discovered.add(link)
                            queue.append((link, depth + 1))

                        if len(discovered) >= max_pages:
                            break

                except Exception as exc:
                    logger.debug("Discovery error for %s: %s", current_url, exc)

        result = list(discovered)[:max_pages]
        logger.info("Discovery complete for %s: %d URLs found", self.origin, len(result))
        return result

    # ------------------------------------------------------------------
    # HTTP crawl
    # ------------------------------------------------------------------

    async def _crawl_with_httpx(
        self,
        client: httpx.AsyncClient,
        url: str,
    ) -> CrawlResult:
        """Fetch a page with HTTPX, retrying a timeout once.

        The initial request and each redirect hop get one retry on
        ``httpx.TimeoutException``. SSRF validation is still performed before
        every redirect request.
        """
        current_url = url
        raw_html = ""
        http_status = 0
        content_type = ""
        hops = 0

        async def _get_with_timeout_retry(target_url: str) -> httpx.Response:
            """GET *target_url*, retrying exactly once if it times out."""
            last_timeout: Optional[httpx.TimeoutException] = None

            for attempt in range(2):
                try:
                    return await client.get(target_url)
                except httpx.TimeoutException as exc:
                    last_timeout = exc

                    if attempt == 0:
                        logger.warning(
                            "HTTP timeout for %s — retrying once after 1s",
                            target_url,
                        )
                        await asyncio.sleep(1.0)
                        continue

                    raise

            # Defensive fallback; loop above always returns or raises.
            if last_timeout is not None:
                raise last_timeout

            raise httpx.RequestError(
                "HTTP request failed without a response",
                request=httpx.Request("GET", target_url),
            )

        try:
            resp = await _get_with_timeout_retry(current_url)
            http_status = resp.status_code

            # Manual redirect following with SSRF re-validation.
            while resp.is_redirect and hops < self.settings.MAX_REDIRECTS:
                location = resp.headers.get("location", "")

                if not location:
                    return _build_failed_result(
                        url=url,
                        http_status=resp.status_code,
                        error_code="INVALID_REDIRECT",
                        error_message="Redirect response did not include a Location header.",
                    )

                redirect_target = urljoin(current_url, location)

                try:
                    redirect_target = validate_url(redirect_target)
                except ValueError as exc:
                    return _build_failed_result(
                        url=url,
                        http_status=resp.status_code,
                        error_code="SSRF_REDIRECT_BLOCKED",
                        error_message=str(exc),
                    )

                resp = await _get_with_timeout_retry(redirect_target)
                current_url = redirect_target
                http_status = resp.status_code
                hops += 1

            # Explicitly reject redirect chains longer than our configured cap.
            if resp.is_redirect:
                return _build_failed_result(
                    url=url,
                    http_status=resp.status_code,
                    error_code="TOO_MANY_REDIRECTS",
                    error_message=(
                        f"Redirect chain exceeded MAX_REDIRECTS="
                        f"{self.settings.MAX_REDIRECTS}."
                    ),
                )

            content_type = resp.headers.get("content-type", "")
            raw_html = resp.text

        except httpx.TimeoutException as exc:
            logger.warning(
                "HTTP request timed out after one retry: %s",
                current_url,
            )
            return _build_failed_result(
                url=url,
                http_status=0,
                error_code="HTTP_TIMEOUT",
                error_message=str(exc) or f"Request timed out for {current_url}",
            )

        except httpx.RequestError as exc:
            return _build_failed_result(
                url=url,
                http_status=0,
                error_code="HTTP_REQUEST_ERROR",
                error_message=str(exc),
            )

        if http_status != 200:
            return _build_failed_result(
                url=url,
                http_status=http_status,
                error_code=f"HTTP_{http_status}",
                error_message=f"Non-200 HTTP status: {http_status}",
            )

        # Only HTML/XHTML should enter the HTML extractor.
        if (
            "text/html" not in content_type.lower()
            and "application/xhtml" not in content_type.lower()
        ):
            return _build_failed_result(
                url=url,
                http_status=http_status,
                error_code="UNSUPPORTED_CONTENT_TYPE",
                error_message=f"Unsupported Content-Type: {content_type or 'unknown'}",
            )

        try:
            page = extract_page_content(raw_html, current_url)
        except Exception as exc:
            return _build_failed_result(
                url=url,
                http_status=http_status,
                error_code="EXTRACTION_ERROR",
                error_message=str(exc),
            )

        soup = BeautifulSoup(raw_html, "html.parser")
        canonical = _extract_canonical(soup, current_url)

        return CrawlResult(
            url=url,
            canonical_url=canonical,
            title=page.title,
            http_status=http_status,
            content_type=content_type,
            raw_html=raw_html,
            clean_text=page.clean_text,
            structured_data=page.structured_data,
            content_hash=_sha256(page.clean_text),
            crawl_status="SUCCESS",
            render_mode="HTTP",
        )

    # ------------------------------------------------------------------
    # Playwright crawl
    # ------------------------------------------------------------------

    async def _crawl_with_playwright(self, url: str) -> CrawlResult:
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            return _build_failed_result(
                url=url,
                http_status=0,
                error_code="PLAYWRIGHT_NOT_INSTALLED",
                error_message="playwright package is not installed.",
                render_mode="PLAYWRIGHT",
            )

        timeout_ms = self.settings.BROWSER_NAV_TIMEOUT_SECONDS * 1000
        raw_html = ""
        http_status = 0

        try:
            async with async_playwright() as pw:
                browser = await pw.chromium.launch(headless=True)

                context = await browser.new_context(
                    user_agent=_USER_AGENT,
                    extra_http_headers={"Accept-Language": "en-US,en;q=0.9"},
                )

                await self._install_browser_ssrf_guard(context)
                page = await context.new_page()

                try:
                    response = await page.goto(
                        url,
                        timeout=timeout_ms,
                        wait_until="domcontentloaded",
                    )

                    try:
                        await page.wait_for_load_state("networkidle", timeout=3000)
                    except Exception:
                        await asyncio.sleep(0.75)

                    http_status = response.status if response else 0
                    raw_html = await page.content()

                finally:
                    await browser.close()

        except Exception as exc:
            return _build_failed_result(
                url=url,
                http_status=http_status,
                error_code="PLAYWRIGHT_ERROR",
                error_message=str(exc),
                render_mode="PLAYWRIGHT",
            )

        if http_status != 200:
            return _build_failed_result(
                url=url,
                http_status=http_status,
                error_code=f"HTTP_{http_status}",
                error_message=f"Playwright got non-200 status: {http_status}",
                render_mode="PLAYWRIGHT",
            )

        try:
            page_data = extract_page_content(raw_html, url)
        except Exception as exc:
            return _build_failed_result(
                url=url,
                http_status=http_status,
                error_code="EXTRACTION_ERROR",
                error_message=str(exc),
                render_mode="PLAYWRIGHT",
            )

        soup = BeautifulSoup(raw_html, "html.parser")
        canonical = _extract_canonical(soup, url)

        return CrawlResult(
            url=url,
            canonical_url=canonical,
            title=page_data.title,
            http_status=http_status,
            content_type="text/html",
            raw_html=raw_html,
            clean_text=page_data.clean_text,
            structured_data=page_data.structured_data,
            content_hash=_sha256(page_data.clean_text),
            crawl_status="SUCCESS",
            render_mode="PLAYWRIGHT",
        )

    # ------------------------------------------------------------------
    # Rendered branding
    # ------------------------------------------------------------------

    async def extract_rendered_branding(self, url: str) -> dict[str, Any]:
        """Render the root page and inspect computed styles/visible DOM.

        This is intentionally a dedicated operation. It runs even when the HTTP
        page already contains enough text and therefore would not normally
        trigger the SPA fallback.
        """

        try:
            from playwright.async_api import async_playwright
        except ImportError:
            logger.warning("Rendered branding skipped: Playwright is not installed")
            return {}

        try:
            safe_url = validate_url(normalize_url(url))
        except ValueError as exc:
            logger.warning("Rendered branding URL blocked: %s", exc)
            return {}

        timeout_ms = self.settings.BROWSER_NAV_TIMEOUT_SECONDS * 1000

        script = r"""
        () => {
            const toHex = (value) => {
                if (!value) return null;

                const v = String(value).trim();

                if (/^#[0-9a-f]{6}$/i.test(v)) {
                    return v.toUpperCase();
                }

                if (/^#[0-9a-f]{3}$/i.test(v)) {
                    return (
                        "#" +
                        v.slice(1).split("").map(c => c + c).join("")
                    ).toUpperCase();
                }

                const m = v.match(
                    /rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)/
                );

                if (!m) return null;

                const parts = [m[1], m[2], m[3]]
                    .map(Number)
                    .map(n => Math.max(0, Math.min(255, n)));

                return "#" + parts
                    .map(n => n.toString(16).padStart(2, "0"))
                    .join("")
                    .toUpperCase();
            };

            const rgb = (hex) => {
                if (!hex || !/^#[0-9A-F]{6}$/.test(hex)) return null;
                return [
                    parseInt(hex.slice(1, 3), 16),
                    parseInt(hex.slice(3, 5), 16),
                    parseInt(hex.slice(5, 7), 16),
                ];
            };

            const neutral = (hex) => {
                const c = rgb(hex);
                if (!c) return true;

                const [r, g, b] = c;

                if (r >= 245 && g >= 245 && b >= 245) return true;
                if (r <= 20 && g <= 20 && b <= 20) return true;
                if (Math.max(r, g, b) - Math.min(r, g, b) < 15) return true;

                return false;
            };

            const visible = (el) => {
                if (!el) return false;

                const style = getComputedStyle(el);
                const rect = el.getBoundingClientRect();

                return (
                    style.display !== "none" &&
                    style.visibility !== "hidden" &&
                    Number(style.opacity || 1) > 0.05 &&
                    rect.width > 1 &&
                    rect.height > 1
                );
            };

            // Evidence-based brand-color scoring.
            // Do not let toast/chat/cookie/recaptcha widgets dominate branding.
            const colorScores = new Map();

            const descriptorOf = (el) => [
                el?.className || "",
                el?.id || "",
                el?.getAttribute?.("aria-label") || "",
                el?.getAttribute?.("name") || "",
                el?.textContent || "",
            ].join(" ").toLowerCase();

            const noiseTokens = [
                "toast", "notification", "snackbar", "cookie", "consent",
                "gdpr", "recaptcha", "captcha", "intercom", "crisp", "tawk",
                "whatsapp", "chat-widget", "chatbot", "launcher",
                "accessibility", "onesignal", "hotjar"
            ];

            const isNoise = (el) => {
                let node = el;
                for (let depth = 0; node && depth < 4; depth++, node = node.parentElement) {
                    const descriptor = descriptorOf(node);
                    if (noiseTokens.some(token => descriptor.includes(token))) return true;
                }
                return false;
            };

            const inViewport = (el) => {
                const rect = el.getBoundingClientRect();
                return rect.bottom > 0 && rect.top < window.innerHeight * 1.5;
            };

            const addColor = (value, weight = 1) => {
                const hex = toHex(value);
                if (!hex || neutral(hex)) return;
                colorScores.set(hex, (colorScores.get(hex) || 0) + weight);
            };

            // Header/navigation is one of the strongest site-wide brand signals.
            for (const el of document.querySelectorAll(
                'header, nav, [role="navigation"], [class*="navbar"], [class*="header"]'
            )) {
                if (!visible(el) || isNoise(el)) continue;
                const style = getComputedStyle(el);
                addColor(style.backgroundColor, 10);
                addColor(style.borderColor, 2);
            }

            // Above-the-fold hero/banner regions are strong brand signals.
            for (const el of document.querySelectorAll(
                'main section, [class*="hero"], [id*="hero"], [class*="banner"]'
            )) {
                if (!visible(el) || !inViewport(el) || isNoise(el)) continue;
                const style = getComputedStyle(el);
                addColor(style.backgroundColor, 5);
                addColor(style.borderColor, 1);
            }

            // Only score visible, above-fold CTA-like controls. Ordinary links
            // no longer receive a blanket brand-color score.
            for (const el of document.querySelectorAll(
                'button, a, [role="button"], input[type="submit"]'
            )) {
                if (!visible(el) || !inViewport(el) || isNoise(el)) continue;

                const style = getComputedStyle(el);
                const descriptor = descriptorOf(el);
                const inHeader = !!el.closest(
                    'header, nav, [role="navigation"], [class*="navbar"], [class*="header"]'
                );

                const strongCTA = [
                    "primary", "cta", "get started", "contact", "book",
                    "demo", "start", "learn more", "talk to", "schedule"
                ].some(token => descriptor.includes(token));

                // Ignore generic links unless they have a real CTA/header signal.
                if (el.tagName === "A" && !strongCTA && !inHeader) continue;

                let weight = 2;
                if (strongCTA) weight += 6;
                if (inHeader) weight += 3;

                addColor(style.backgroundColor, weight);
                addColor(style.borderColor, 1);
            }

            // Explicit root-level brand variables are valuable, but distinguish
            // primary/brand from weaker secondary/accent evidence.
            const rootStyle = getComputedStyle(document.documentElement);

            for (let i = 0; i < rootStyle.length; i++) {
                const name = rootStyle[i];
                if (!name || !name.startsWith("--")) continue;

                const lower = name.toLowerCase();
                const value = rootStyle.getPropertyValue(name);

                if (lower.includes("brand") || lower.includes("primary")) {
                    addColor(value, 14);
                } else if (lower.includes("secondary")) {
                    addColor(value, 9);
                } else if (lower.includes("accent")) {
                    addColor(value, 7);
                }
            }

            const rankedRaw = Array.from(colorScores.entries())
                .sort((a, b) => b[1] - a[1])
                .map(([color]) => color);

            // Avoid returning three almost-identical shades as the palette.
            const colorDistance = (a, b) => {
                const ca = rgb(a);
                const cb = rgb(b);
                if (!ca || !cb) return 999;
                return Math.sqrt(
                    Math.pow(ca[0] - cb[0], 2) +
                    Math.pow(ca[1] - cb[1], 2) +
                    Math.pow(ca[2] - cb[2], 2)
                );
            };

            const ranked = [];
            for (const color of rankedRaw) {
                if (ranked.every(existing => colorDistance(existing, color) >= 45)) {
                    ranked.push(color);
                }
                if (ranked.length >= 3) break;
            }

            const bodyStyle = document.body
                ? getComputedStyle(document.body)
                : null;

            const htmlStyle = getComputedStyle(document.documentElement);

            const background =
                toHex(bodyStyle?.backgroundColor) ||
                toHex(htmlStyle.backgroundColor);

            const textColor =
                toHex(bodyStyle?.color) ||
                toHex(htmlStyle.color);

            const fontFamily =
                bodyStyle?.fontFamily ||
                htmlStyle.fontFamily ||
                null;

            // Score logo images from the rendered DOM.
            const logoCandidates = [];

            for (const img of document.querySelectorAll("img")) {
                if (!visible(img)) continue;

                const src = img.currentSrc || img.src || "";
                if (!src) continue;

                const descriptor = [
                    img.alt || "",
                    img.id || "",
                    img.className || "",
                    src,
                    img.parentElement?.className || "",
                    img.closest("header, nav") ? "header-nav" : "",
                ].join(" ").toLowerCase();

                let score = 0;

                if (descriptor.includes("logo")) score += 12;
                if (descriptor.includes("brand")) score += 6;
                if (img.closest("header, nav")) score += 5;

                const rect = img.getBoundingClientRect();

                if (rect.width >= 40 && rect.width <= 500) score += 2;
                if (rect.height >= 20 && rect.height <= 250) score += 2;

                if (score > 0) {
                    logoCandidates.push({src, score});
                }
            }

            logoCandidates.sort((a, b) => b.score - a.score);

            return {
                logo_url: logoCandidates[0]?.src || null,
                primary_color: ranked[0] || null,
                secondary_color: ranked[1] || ranked[0] || null,
                accent_color: ranked[2] || ranked[1] || ranked[0] || null,
                background_color: background || null,
                text_color: textColor || null,
                font_family: fontFamily || null,
            };
        }
        """

        try:
            async with async_playwright() as pw:
                browser = await pw.chromium.launch(headless=True)

                context = await browser.new_context(
                    user_agent=_USER_AGENT,
                    extra_http_headers={"Accept-Language": "en-US,en;q=0.9"},
                )

                await self._install_browser_ssrf_guard(context)
                page = await context.new_page()

                try:
                    response = await page.goto(
                        safe_url,
                        timeout=timeout_ms,
                        wait_until="domcontentloaded",
                    )

                    if response and response.status >= 400:
                        logger.warning(
                            "Rendered branding received HTTP %s for %s",
                            response.status,
                            safe_url,
                        )
                        return {}

                    try:
                        await page.wait_for_load_state("networkidle", timeout=5000)
                    except Exception:
                        await asyncio.sleep(1.0)

                    final_url = page.url

                    try:
                        validate_url(final_url)
                    except ValueError as exc:
                        logger.warning(
                            "Rendered branding final URL blocked by SSRF policy: %s",
                            exc,
                        )
                        return {}

                    result = await page.evaluate(script)

                    if isinstance(result, dict):
                        logger.info(
                            "Rendered branding extracted for %s: logo=%s primary=%s font=%s",
                            safe_url,
                            bool(result.get("logo_url")),
                            result.get("primary_color"),
                            result.get("font_family"),
                        )
                        return result

                    return {}

                finally:
                    await browser.close()

        except Exception as exc:
            logger.warning("Rendered branding extraction failed for %s: %s", safe_url, exc)
            return {}

    # ------------------------------------------------------------------
    # Single-page entry point
    # ------------------------------------------------------------------

    async def crawl_page(self, url: str) -> CrawlResult:
        try:
            url = validate_url(normalize_url(url))
        except ValueError as exc:
            return _build_failed_result(
                url=url,
                http_status=0,
                error_code="SSRF_BLOCKED",
                error_message=str(exc),
            )

        timeout = httpx.Timeout(self.settings.HTTP_TIMEOUT_SECONDS)

        async with httpx.AsyncClient(
            headers=self._http_headers,
            timeout=timeout,
            follow_redirects=False,
            max_redirects=0,
        ) as client:
            result = await self._crawl_with_httpx(client, url)

        if result.crawl_status == "SUCCESS" and _is_spa(
            result.raw_html,
            result.clean_text,
        ):
            logger.info(
                "SPA detected at %s (text_len=%d), triggering Playwright fallback.",
                url,
                len(result.clean_text),
            )

            playwright_result = await self._crawl_with_playwright(url)

            if playwright_result.crawl_status == "SUCCESS":
                return playwright_result

            logger.warning(
                "Playwright fallback failed for %s: %s",
                url,
                playwright_result.error_message,
            )

        return result

    # ------------------------------------------------------------------
    # Batch crawl
    # ------------------------------------------------------------------

    async def crawl_all(
        self,
        urls: list[str],
        concurrency: int = 5,
    ) -> list[CrawlResult]:
        semaphore = asyncio.Semaphore(concurrency)
        results: list[CrawlResult | None] = [None] * len(urls)

        async def _task(idx: int, url: str) -> None:
            async with semaphore:
                try:
                    results[idx] = await self.crawl_page(url)
                except Exception as exc:
                    logger.exception("Unexpected error crawling %s: %s", url, exc)
                    results[idx] = _build_failed_result(
                        url=url,
                        http_status=0,
                        error_code="UNEXPECTED_ERROR",
                        error_message=str(exc),
                    )

        tasks = [
            asyncio.create_task(_task(i, url))
            for i, url in enumerate(urls)
        ]

        await asyncio.gather(*tasks)

        return [
            result
            for result in results
            if result is not None
        ]
