"""
Content Extractor — PRD Sections 6.1.5 and 6.4.2

Provides two top-level functions:

- ``extract_page_content``:
    Removes boilerplate, isolates the primary content container, and returns
    structured page content suitable for knowledge-base generation.

- ``extract_branding``:
    Extracts visual branding signals from the page HTML including company name,
    logo, favicon, colors, and font family with per-field confidence scores.

Important:
    This module intentionally performs no network requests. It extracts branding
    from the HTML, embedded CSS, inline CSS, metadata, and asset references
    already present in the crawled page.

    External stylesheet fetching should be handled separately through the
    crawler/network-safety layer.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup, Tag


# ===========================================================================
# Data classes
# ===========================================================================


@dataclass
class ExtractedPage:
    """Structured representation of a crawled and cleaned HTML page."""

    title: str
    description: str
    headings: List[Dict[str, str]]
    clean_text: str
    structured_data: Dict[str, Any]


@dataclass
class ExtractedBranding:
    """Visual brand identity extracted from a website."""

    company_name: Optional[str]
    logo_url: Optional[str]
    favicon_url: Optional[str]

    primary_color: Optional[str]
    secondary_color: Optional[str]
    background_color: Optional[str]
    text_color: Optional[str]
    accent_color: Optional[str]
    font_family: Optional[str]

    confidence: Dict[str, float] = field(default_factory=dict)


# ===========================================================================
# Content extraction constants
# ===========================================================================


_NOISE_TAGS: tuple[str, ...] = (
    "script",
    "style",
    "noscript",
    "svg",
    "canvas",
    "nav",
    "footer",
    "header",
    "aside",
    "form",
    "button",
    "iframe",
    "object",
    "embed",
)


_CONSENT_SELECTORS: tuple[str, ...] = (
    "[class*='cookie']",
    "[id*='consent']",
    "[class*='banner']",
    "[class*='gdpr']",
    "[id*='cookie']",
    "[class*='popup']",
    "[id*='popup']",
    "[class*='overlay']",
    "[id*='overlay']",
)


_CONTENT_SELECTORS: tuple[str, ...] = (
    "main",
    "article",
    "[role='main']",
    "#main-content",
    "#content",
    ".content",
    ".main-content",
    ".post-content",
    ".entry-content",
    ".page-content",
    "section",
)


# ===========================================================================
# Branding regexes/constants
# ===========================================================================


HEX_COLOR_RE = re.compile(
    r"#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b"
)


RGB_COLOR_RE = re.compile(
    r"rgba?\(\s*"
    r"(\d{1,3})\s*,\s*"
    r"(\d{1,3})\s*,\s*"
    r"(\d{1,3})",
    re.IGNORECASE,
)


FONT_FAMILY_RE = re.compile(
    r"font-family\s*:\s*([^;}{]+)",
    re.IGNORECASE,
)


CSS_PRIMARY_VAR_RE = re.compile(
    r"--(?:"
    r"primary|"
    r"brand|"
    r"brand-color|"
    r"primary-color|"
    r"color-primary|"
    r"accent|"
    r"accent-color"
    r")\s*:\s*"
    r"(#[0-9a-fA-F]{3,6})",
    re.IGNORECASE,
)


BACKGROUND_COLOR_RE = re.compile(
    r"background(?:-color)?\s*:\s*"
    r"(#[0-9a-fA-F]{3,6})",
    re.IGNORECASE,
)


TEXT_COLOR_RE = re.compile(
    r"(?:^|;)\s*color\s*:\s*"
    r"(#[0-9a-fA-F]{3,6})",
    re.IGNORECASE,
)


_LOGO_KEYWORDS_RE = re.compile(
    r"(?:^|[\s_\-])(?:logo|brand|site-logo|navbar-logo)(?:$|[\s_\-])",
    re.IGNORECASE,
)


# ===========================================================================
# Generic helpers
# ===========================================================================


def _make_soup(html: str) -> BeautifulSoup:
    """Parse HTML using lxml where available."""

    try:
        return BeautifulSoup(html, "lxml")
    except Exception:
        return BeautifulSoup(html, "html.parser")


def _resolve_url(href: str, base_url: str) -> str:
    """Resolve a relative asset URL against the page URL."""

    try:
        return urljoin(base_url, href)
    except Exception:
        return href


# ===========================================================================
# Content extraction helpers
# ===========================================================================


def _remove_noise(soup: BeautifulSoup) -> None:
    """Remove boilerplate and consent elements."""

    for tag in _NOISE_TAGS:
        for element in soup.find_all(tag):
            element.decompose()

    for selector in _CONSENT_SELECTORS:
        try:
            for element in soup.select(selector):
                element.decompose()
        except Exception:
            # Malformed selector/content should never kill extraction.
            continue


def _text_density(tag: Tag) -> float:
    """Visible text characters divided by HTML characters."""

    html_len = len(str(tag))

    if html_len == 0:
        return 0.0

    text_len = len(
        tag.get_text(
            separator=" ",
            strip=True,
        )
    )

    return text_len / html_len


def _find_primary_container(soup: BeautifulSoup) -> Tag:
    """Locate the most likely primary content container."""

    for selector in _CONTENT_SELECTORS:
        element = soup.select_one(selector)

        if (
            element
            and len(element.get_text(strip=True)) > 50
        ):
            return element

    body = soup.find("body") or soup

    candidates = body.find_all(
        ["div", "section"],
        recursive=True,
    )

    if candidates:
        best = max(
            candidates,
            key=lambda element: len(
                element.get_text(strip=True)
            ),
            default=None,
        )

        if best:
            return best

    return soup  # type: ignore[return-value]


def _extract_headings(
    container: Tag,
) -> list[dict[str, str]]:
    """Extract h1-h6 elements in document order."""

    headings: list[dict[str, str]] = []

    for tag in container.find_all(
        re.compile(r"^h[1-6]$")
    ):
        text = tag.get_text(
            separator=" ",
            strip=True,
        )

        if text:
            headings.append(
                {
                    "level": tag.name,
                    "text": text,
                }
            )

    return headings


def _extract_structured_data(
    container: Tag,
) -> dict[str, Any]:
    """Extract paragraphs, list items, and tables."""

    paragraphs: list[str] = []

    for paragraph in container.find_all("p"):
        text = paragraph.get_text(
            separator=" ",
            strip=True,
        )

        if text:
            paragraphs.append(text)

    list_items: list[str] = []

    for item in container.find_all("li"):
        text = item.get_text(
            separator=" ",
            strip=True,
        )

        if text:
            list_items.append(text)

    tables: list[list[list[str]]] = []

    for table in container.find_all("table"):
        rows: list[list[str]] = []

        for row in table.find_all("tr"):
            cells = [
                cell.get_text(
                    separator=" ",
                    strip=True,
                )
                for cell in row.find_all(
                    ["td", "th"]
                )
            ]

            if cells:
                rows.append(cells)

        if rows:
            tables.append(rows)

    return {
        "paragraphs": paragraphs,
        "list_items": list_items,
        "tables": tables,
    }


# ===========================================================================
# Branding/color helpers
# ===========================================================================


def _normalize_hex(
    color: str,
) -> Optional[str]:
    """Normalize #RGB or #RRGGBB into uppercase #RRGGBB."""

    if not color:
        return None

    color = color.strip().upper()

    if re.fullmatch(
        r"#[0-9A-F]{3}",
        color,
    ):
        color = "#" + "".join(
            char * 2
            for char in color[1:]
        )

    if re.fullmatch(
        r"#[0-9A-F]{6}",
        color,
    ):
        return color

    return None


def _rgb_to_hex(
    r: int,
    g: int,
    b: int,
) -> Optional[str]:
    """Convert RGB components into a hex color."""

    if not all(
        0 <= value <= 255
        for value in (r, g, b)
    ):
        return None

    return f"#{r:02X}{g:02X}{b:02X}"


def _hex_rgb(
    color: str,
) -> tuple[int, int, int]:
    """Convert normalized hex color into RGB."""

    value = color.lstrip("#")

    return (
        int(value[0:2], 16),
        int(value[2:4], 16),
        int(value[4:6], 16),
    )


def _relative_luminance(
    color: str,
) -> float:
    """Approximate relative luminance for theme decisions."""

    r, g, b = _hex_rgb(color)

    def convert(channel: int) -> float:
        value = channel / 255.0

        if value <= 0.03928:
            return value / 12.92

        return (
            (value + 0.055) / 1.055
        ) ** 2.4

    return (
        0.2126 * convert(r)
        + 0.7152 * convert(g)
        + 0.0722 * convert(b)
    )


def _is_neutral_color(
    color: str,
) -> bool:
    """Return True for near-white, near-black, or gray colors."""

    r, g, b = _hex_rgb(color)

    # Near-white
    if (
        r >= 245
        and g >= 245
        and b >= 245
    ):
        return True

    # Near-black
    if (
        r <= 20
        and g <= 20
        and b <= 20
    ):
        return True

    # Low-saturation gray
    if (
        max(r, g, b)
        - min(r, g, b)
        < 15
    ):
        return True

    return False


def _extract_colors_from_css(
    css: str,
) -> list[str]:
    """Extract normalized HEX and RGB colors from CSS."""

    colors: list[str] = []

    for match in HEX_COLOR_RE.findall(css):
        normalized = _normalize_hex(match)

        if normalized:
            colors.append(normalized)

    for match in RGB_COLOR_RE.findall(css):
        converted = _rgb_to_hex(
            int(match[0]),
            int(match[1]),
            int(match[2]),
        )

        if converted:
            colors.append(converted)

    return colors


def _choose_brand_colors(
    weighted_colors: list[str],
) -> tuple[
    Optional[str],
    Optional[str],
    Optional[str],
]:
    """Select primary, secondary and accent colors.

    Neutral colors are removed because white/black/gray are frequently
    structural UI colors rather than actual brand colors.
    """

    filtered = [
        color
        for color in weighted_colors
        if not _is_neutral_color(color)
    ]

    if not filtered:
        return None, None, None

    counts = Counter(filtered)

    ranked = [
        color
        for color, _count
        in counts.most_common()
    ]

    primary = (
        ranked[0]
        if ranked
        else None
    )

    secondary = (
        ranked[1]
        if len(ranked) > 1
        else primary
    )

    accent = (
        ranked[2]
        if len(ranked) > 2
        else secondary
    )

    return (
        primary,
        secondary,
        accent,
    )


def _clean_font_family(
    value: str,
) -> Optional[str]:
    """Clean a CSS font-family declaration."""

    if not value:
        return None

    value = " ".join(
        value.strip().split()
    )

    # Prevent accidentally storing huge malformed CSS fragments.
    if len(value) > 200:
        return None

    return value


# ===========================================================================
# Logo / favicon helpers
# ===========================================================================


def _extract_favicon(
    soup: BeautifulSoup,
    base_url: str,
) -> tuple[Optional[str], float]:
    """Find the highest-confidence favicon."""

    candidates = (
        "icon",
        "shortcut icon",
        "apple-touch-icon",
        "mask-icon",
    )

    for link in soup.find_all("link"):
        rel_value = link.get("rel", [])

        if isinstance(rel_value, str):
            rel_tokens = [rel_value.lower()]
        else:
            rel_tokens = [
                str(value).lower()
                for value in rel_value
            ]

        joined_rel = " ".join(rel_tokens)

        if any(
            candidate in joined_rel
            for candidate in candidates
        ):
            href = link.get("href")

            if href:
                return (
                    _resolve_url(
                        str(href),
                        base_url,
                    ),
                    0.90,
                )

    parsed = urlparse(base_url)

    if parsed.scheme and parsed.netloc:
        return (
            f"{parsed.scheme}://"
            f"{parsed.netloc}/favicon.ico",
            0.30,
        )

    return None, 0.0


def _extract_logo(
    soup: BeautifulSoup,
    base_url: str,
) -> tuple[Optional[str], float]:
    """Find the best logo candidate from metadata and page markup."""

    # ------------------------------------------------------------------
    # 1. Explicit image with logo-like attributes
    # ------------------------------------------------------------------

    scored_candidates: list[
        tuple[int, str]
    ] = []

    for image in soup.find_all("img"):
        src = (
            image.get("src")
            or image.get("data-src")
            or image.get("data-lazy-src")
        )

        if not src:
            continue

        alt = str(
            image.get("alt", "")
        )

        image_id = str(
            image.get("id", "")
        )

        classes = image.get(
            "class",
            [],
        )

        if isinstance(classes, str):
            class_text = classes
        else:
            class_text = " ".join(
                str(item)
                for item in classes
            )

        src_text = str(src)

        searchable = " ".join(
            [
                alt,
                image_id,
                class_text,
                src_text,
            ]
        )

        score = 0

        if _LOGO_KEYWORDS_RE.search(
            searchable
        ):
            score += 10

        parent = image.parent

        if isinstance(parent, Tag):
            if parent.name in {
                "header",
                "nav",
            }:
                score += 5

            parent_classes = parent.get(
                "class",
                [],
            )

            if isinstance(
                parent_classes,
                str,
            ):
                parent_class_text = (
                    parent_classes
                )
            else:
                parent_class_text = " ".join(
                    str(item)
                    for item in parent_classes
                )

            if _LOGO_KEYWORDS_RE.search(
                parent_class_text
            ):
                score += 4

        if score > 0:
            scored_candidates.append(
                (
                    score,
                    _resolve_url(
                        src_text,
                        base_url,
                    ),
                )
            )

    if scored_candidates:
        scored_candidates.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        return (
            scored_candidates[0][1],
            0.90,
        )

    # ------------------------------------------------------------------
    # 2. OpenGraph image as weaker fallback
    # ------------------------------------------------------------------

    og_image = soup.find(
        "meta",
        property="og:image",
    )

    if (
        og_image
        and og_image.get("content")
    ):
        return (
            _resolve_url(
                str(
                    og_image["content"]
                ),
                base_url,
            ),
            0.55,
        )

    # ------------------------------------------------------------------
    # 3. Apple touch icon
    # ------------------------------------------------------------------

    for link in soup.find_all("link"):
        rel_value = link.get(
            "rel",
            [],
        )

        if isinstance(rel_value, str):
            rel_text = rel_value.lower()
        else:
            rel_text = " ".join(
                str(value).lower()
                for value in rel_value
            )

        if (
            "apple-touch-icon"
            in rel_text
            and link.get("href")
        ):
            return (
                _resolve_url(
                    str(link["href"]),
                    base_url,
                ),
                0.50,
            )

    return None, 0.0


# ===========================================================================
# Public content API
# ===========================================================================


def extract_page_content(
    html: str,
    url: str,
) -> ExtractedPage:
    """Extract clean structured content from raw HTML."""

    soup = _make_soup(html)

    # ------------------------------------------------------------------
    # Title
    # ------------------------------------------------------------------

    title_tag = soup.find("title")

    title = (
        title_tag.get_text(strip=True)
        if title_tag
        else ""
    )

    # ------------------------------------------------------------------
    # Meta description
    # ------------------------------------------------------------------

    meta_desc_tag = soup.find(
        "meta",
        attrs={
            "name": re.compile(
                r"^description$",
                re.I,
            )
        },
    )

    description = ""

    if (
        meta_desc_tag
        and meta_desc_tag.get("content")
    ):
        description = str(
            meta_desc_tag["content"]
        ).strip()

    # ------------------------------------------------------------------
    # Remove boilerplate
    # ------------------------------------------------------------------

    _remove_noise(soup)

    # ------------------------------------------------------------------
    # Primary content
    # ------------------------------------------------------------------

    container = _find_primary_container(
        soup
    )

    headings = _extract_headings(
        container
    )

    # Fallback title from first H1.
    if not title and headings:
        first_h1 = next(
            (
                heading["text"]
                for heading in headings
                if heading["level"] == "h1"
            ),
            None,
        )

        if first_h1:
            title = first_h1

    structured_data = (
        _extract_structured_data(
            container
        )
    )

    raw_text = container.get_text(
        separator="\n",
        strip=True,
    )

    lines = [
        line.strip()
        for line in raw_text.splitlines()
        if line.strip()
    ]

    clean_text = "\n".join(lines)

    return ExtractedPage(
        title=title,
        description=description,
        headings=headings,
        clean_text=clean_text,
        structured_data=structured_data,
    )


# ===========================================================================
# Public branding API
# ===========================================================================


def extract_branding(
    html: str,
    base_url: str,
) -> ExtractedBranding:
    """Extract branding signals from homepage HTML.

    Current extraction sources:

    Company:
        og:site_name
        application-name
        title
        h1

    Logo:
        logo-like <img>
        og:image
        apple-touch-icon

    Favicon:
        icon / shortcut icon / apple-touch-icon / mask-icon

    Colors:
        meta theme-color
        CSS custom properties
        embedded <style>
        inline style attributes
        CTA/button inline colors

    Font:
        embedded CSS
        inline CSS

    No network requests are performed here.
    """

    soup = _make_soup(html)

    confidence: dict[
        str,
        float,
    ] = {}

    # ===================================================================
    # Company name
    # ===================================================================

    company_name: Optional[str] = None
    name_confidence = 0.0

    og_site_name = soup.find(
        "meta",
        property="og:site_name",
    )

    if (
        og_site_name
        and og_site_name.get("content")
    ):
        company_name = str(
            og_site_name["content"]
        ).strip()

        name_confidence = 0.95

    if not company_name:
        application_name = soup.find(
            "meta",
            attrs={
                "name": "application-name"
            },
        )

        if (
            application_name
            and application_name.get(
                "content"
            )
        ):
            company_name = str(
                application_name[
                    "content"
                ]
            ).strip()

            name_confidence = 0.85

    if not company_name:
        title_tag = soup.find("title")

        if title_tag:
            raw_title = (
                title_tag.get_text(
                    strip=True
                )
            )

            for separator in (
                " | ",
                " - ",
                " — ",
                " :: ",
                " · ",
                " – ",
            ):
                if separator in raw_title:
                    raw_title = (
                        raw_title
                        .split(separator)[0]
                        .strip()
                    )
                    break

            # Handle SEO titles such as:
            # "Cyberify: AI Solutions & Custom Software for Business Growth"
            # Only split on ":" when the left side looks like a short brand
            # name and the right side looks like a descriptive tagline.
            if ":" in raw_title:
                left, right = raw_title.split(":", 1)
                left = left.strip()
                right = right.strip()

                if (
                    1 < len(left) <= 50
                    and len(left.split()) <= 6
                    and len(right) >= 8
                ):
                    raw_title = left

            if raw_title:
                company_name = raw_title
                name_confidence = 0.70

    if not company_name:
        heading = soup.find("h1")

        if heading:
            company_name = (
                heading.get_text(
                    separator=" ",
                    strip=True,
                )
            )

            name_confidence = 0.50

    confidence[
        "company_name"
    ] = name_confidence

    # ===================================================================
    # Logo
    # ===================================================================

    (
        logo_url,
        logo_confidence,
    ) = _extract_logo(
        soup,
        base_url,
    )

    confidence[
        "logo_url"
    ] = logo_confidence

    # ===================================================================
    # Favicon
    # ===================================================================

    (
        favicon_url,
        favicon_confidence,
    ) = _extract_favicon(
        soup,
        base_url,
    )

    confidence[
        "favicon_url"
    ] = favicon_confidence

    # ===================================================================
    # Color collection
    # ===================================================================

    color_candidates: list[str] = []

    # -------------------------------------------------------------------
    # theme-color gets very high weighting
    # -------------------------------------------------------------------

    theme_meta = soup.find(
        "meta",
        attrs={
            "name": re.compile(
                r"^theme-color$",
                re.I,
            )
        },
    )

    if (
        theme_meta
        and theme_meta.get("content")
    ):
        theme_color = _normalize_hex(
            str(
                theme_meta[
                    "content"
                ]
            )
        )

        if (
            theme_color
            and not _is_neutral_color(
                theme_color
            )
        ):
            color_candidates.extend(
                [theme_color] * 12
            )

    # -------------------------------------------------------------------
    # Embedded <style>
    # -------------------------------------------------------------------

    embedded_css_parts: list[str] = []

    for style_tag in soup.find_all(
        "style"
    ):
        css_text = style_tag.get_text(
            " ",
            strip=True,
        )

        if not css_text:
            continue

        embedded_css_parts.append(
            css_text
        )

        # General CSS colors.
        color_candidates.extend(
            _extract_colors_from_css(
                css_text
            )
        )

        # Explicit brand/primary CSS variables receive stronger weighting.
        for match in (
            CSS_PRIMARY_VAR_RE.findall(
                css_text
            )
        ):
            normalized = (
                _normalize_hex(match)
            )

            if normalized:
                color_candidates.extend(
                    [normalized] * 10
                )

    # -------------------------------------------------------------------
    # Inline styles
    # -------------------------------------------------------------------

    inline_css_parts: list[str] = []

    for element in soup.find_all(
        style=True
    ):
        inline_style = str(
            element.get(
                "style",
                "",
            )
        )

        if not inline_style:
            continue

        inline_css_parts.append(
            inline_style
        )

        color_candidates.extend(
            _extract_colors_from_css(
                inline_style
            )
        )

    # -------------------------------------------------------------------
    # CTA/button weighting
    # -------------------------------------------------------------------

    for element in soup.find_all(
        ["button", "a"]
    ):
        inline_style = str(
            element.get(
                "style",
                "",
            )
        )

        if not inline_style:
            continue

        button_colors = (
            _extract_colors_from_css(
                inline_style
            )
        )

        for color in button_colors:
            color_candidates.extend(
                [color] * 6
            )

    (
        primary_color,
        secondary_color,
        accent_color,
    ) = _choose_brand_colors(
        color_candidates
    )

    confidence[
        "primary_color"
    ] = (
        0.75
        if primary_color
        else 0.0
    )

    confidence[
        "secondary_color"
    ] = (
        0.65
        if secondary_color
        else 0.0
    )

    confidence[
        "accent_color"
    ] = (
        0.60
        if accent_color
        else 0.0
    )

    # ===================================================================
    # Background color
    # ===================================================================

    background_color: Optional[str] = None
    background_confidence = 0.0

    body = soup.find("body")

    if (
        body
        and body.get("style")
    ):
        body_style = str(
            body.get(
                "style",
                "",
            )
        )

        match = (
            BACKGROUND_COLOR_RE.search(
                body_style
            )
        )

        if match:
            background_color = (
                _normalize_hex(
                    match.group(1)
                )
            )

            if background_color:
                background_confidence = (
                    0.85
                )

    # Search :root/body embedded CSS as secondary source.
    if not background_color:
        combined_embedded_css = "\n".join(
            embedded_css_parts
        )

        body_rule_match = re.search(
            r"(?:body|:root)\s*\{([^}]*)\}",
            combined_embedded_css,
            re.IGNORECASE | re.DOTALL,
        )

        if body_rule_match:
            match = (
                BACKGROUND_COLOR_RE.search(
                    body_rule_match.group(1)
                )
            )

            if match:
                background_color = (
                    _normalize_hex(
                        match.group(1)
                    )
                )

                if background_color:
                    background_confidence = (
                        0.70
                    )

    # Background fallback is intentionally neutral.
    if not background_color:
        background_color = "#FFFFFF"
        background_confidence = 0.40

    confidence[
        "background_color"
    ] = background_confidence

    # ===================================================================
    # Text color
    # ===================================================================

    text_color: Optional[str] = None
    text_confidence = 0.0

    if (
        body
        and body.get("style")
    ):
        body_style = str(
            body.get(
                "style",
                "",
            )
        )

        match = TEXT_COLOR_RE.search(
            body_style
        )

        if match:
            text_color = _normalize_hex(
                match.group(1)
            )

            if text_color:
                text_confidence = 0.85

    if not text_color:
        combined_embedded_css = "\n".join(
            embedded_css_parts
        )

        body_rule_match = re.search(
            r"(?:body|:root)\s*\{([^}]*)\}",
            combined_embedded_css,
            re.IGNORECASE | re.DOTALL,
        )

        if body_rule_match:
            match = TEXT_COLOR_RE.search(
                body_rule_match.group(1)
            )

            if match:
                text_color = (
                    _normalize_hex(
                        match.group(1)
                    )
                )

                if text_color:
                    text_confidence = (
                        0.70
                    )

    # Pick fallback according to background brightness.
    if not text_color:
        if (
            background_color
            and _relative_luminance(
                background_color
            ) < 0.35
        ):
            text_color = "#FFFFFF"
        else:
            text_color = "#111827"

        text_confidence = 0.40

    confidence[
        "text_color"
    ] = text_confidence

    # ===================================================================
    # Font family
    # ===================================================================

    font_candidates: list[str] = []

    for css_text in (
        embedded_css_parts
        + inline_css_parts
    ):
        for match in (
            FONT_FAMILY_RE.findall(
                css_text
            )
        ):
            cleaned = _clean_font_family(
                match
            )

            if cleaned:
                font_candidates.append(
                    cleaned
                )

    font_family: Optional[str] = None
    font_confidence = 0.0

    if font_candidates:
        font_family = (
            Counter(
                font_candidates
            )
            .most_common(1)[0][0]
        )

        font_confidence = 0.65

    confidence[
        "font_family"
    ] = font_confidence

    # ===================================================================
    # Return
    # ===================================================================

    return ExtractedBranding(
        company_name=company_name,
        logo_url=logo_url,
        favicon_url=favicon_url,
        primary_color=primary_color,
        secondary_color=secondary_color,
        background_color=background_color,
        text_color=text_color,
        accent_color=accent_color,
        font_family=font_family,
        confidence=confidence,
    )