"""
URL Normalizer — PRD Section 6.1.2

Provides deterministic URL normalisation, origin extraction, same-origin checking,
and asset-extension detection used throughout the crawl pipeline.
"""

from __future__ import annotations

import re
from urllib.parse import (
    ParseResult,
    parse_qs,
    urlencode,
    urljoin,
    urlparse,
    urlunparse,
)

# ---------------------------------------------------------------------------
# Query parameters that carry no functional meaning and should be stripped.
# ---------------------------------------------------------------------------
_STRIP_PARAMS_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"^utm_", re.IGNORECASE),   # utm_source, utm_medium, utm_campaign, …
    re.compile(r"^fbclid$", re.IGNORECASE),
    re.compile(r"^gclid$", re.IGNORECASE),
    re.compile(r"^ref$", re.IGNORECASE),
    re.compile(r"^mc_eid$", re.IGNORECASE),
    re.compile(r"^_ga$", re.IGNORECASE),
)

# ---------------------------------------------------------------------------
# File extensions that indicate non-HTML assets that should not be crawled.
# ---------------------------------------------------------------------------
_ASSET_EXTENSIONS: frozenset[str] = frozenset(
    {
        ".pdf",
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".svg",
        ".mp4",
        ".zip",
        ".css",
        ".js",
        ".woff",
        ".woff2",
        ".ttf",
        ".eot",
        ".ico",
        ".webp",
        ".avif",
        ".mp3",
        ".wav",
        ".avi",
        ".mov",
        ".xml",   # sitemap XML handled separately in discovery
    }
)


def _is_strip_param(key: str) -> bool:
    """Return True when *key* matches one of the marketing/analytics patterns."""
    return any(pattern.match(key) for pattern in _STRIP_PARAMS_PATTERNS)


def _clean_query_string(query: str) -> str:
    """Remove tracking/analytics query parameters and return sorted remainder."""
    if not query:
        return ""
    params = parse_qs(query, keep_blank_values=True)
    cleaned = {k: v for k, v in params.items() if not _is_strip_param(k)}
    # Sort keys for determinism
    return urlencode(cleaned, doseq=True) if cleaned else ""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def normalize_url(url: str, base_origin: str | None = None) -> str:
    """Return a canonical, deduplicated form of *url*.

    Performs the following transformations:
    - Resolve relative URLs against *base_origin* when provided.
    - Lowercase scheme and hostname.
    - Strip URI fragments.
    - Remove tracking query parameters (utm_*, fbclid, gclid, ref, mc_eid, _ga).
    - Retain functional query parameters.

    Args:
        url:         The raw URL string to normalise.  May be relative.
        base_origin: Optional base URL (e.g. ``"https://example.com"``) used to
                     resolve relative paths such as ``"/about"`` or
                     ``"../contact"``.

    Returns:
        Normalised, absolute URL string.

    Raises:
        ValueError: If the URL cannot be parsed or resolved.
    """
    # Resolve relative URLs
    if base_origin:
        url = urljoin(base_origin.rstrip("/") + "/", url)

    try:
        parsed: ParseResult = urlparse(url.strip())
    except Exception as exc:
        raise ValueError(f"Cannot parse URL '{url}': {exc}") from exc

    # Normalise scheme and host to lowercase
    scheme = (parsed.scheme or "").lower()
    netloc = (parsed.netloc or "").lower()

    # Strip fragment; clean query string
    clean_query = _clean_query_string(parsed.query)

    normalised = urlunparse(
        (scheme, netloc, parsed.path, parsed.params, clean_query, "")
    )
    return normalised


def extract_origin(url: str) -> str:
    """Return the normalised ``scheme://host`` (no path, no query, no fragment).

    Args:
        url: Absolute URL string.

    Returns:
        Lower-cased ``scheme://host[:port]`` string.

    Raises:
        ValueError: If the URL cannot be parsed.
    """
    try:
        parsed = urlparse(url.strip())
    except Exception as exc:
        raise ValueError(f"Cannot parse URL '{url}': {exc}") from exc

    scheme = (parsed.scheme or "").lower()
    # parsed.netloc already contains optional port
    netloc = (parsed.netloc or "").lower()

    if not scheme or not netloc:
        raise ValueError(f"URL '{url}' is missing scheme or host.")

    return f"{scheme}://{netloc}"


def is_same_origin(url: str, origin: str) -> bool:
    """Check whether *url* belongs to the same crawl origin as *origin*.

    Treats ``example.com`` and ``www.example.com`` as equivalent so that the
    crawler stays within the primary site when either variant is submitted.

    Args:
        url:    The candidate URL to test.
        origin: The reference origin (e.g. ``"https://example.com"``).

    Returns:
        True when *url* is same-origin (or same-site www-variant).
    """
    try:
        candidate_host = (urlparse(url).hostname or "").lower().strip(".")
        origin_host = (urlparse(origin).hostname or "").lower().strip(".")
    except Exception:
        return False

    if not candidate_host or not origin_host:
        return False

    # Direct match
    if candidate_host == origin_host:
        return True

    # www equivalence: strip leading "www." from both and compare
    bare_candidate = candidate_host.removeprefix("www.")
    bare_origin = origin_host.removeprefix("www.")

    return bare_candidate == bare_origin


def is_asset_url(url: str) -> bool:
    """Return True when *url* points to a non-HTML binary/media asset.

    Uses the file extension of the URL path to determine asset type.

    Args:
        url: The URL string to test.

    Returns:
        True for known asset extensions (e.g. ``.pdf``, ``.jpg``, ``.js``).
    """
    try:
        path = urlparse(url).path.lower()
    except Exception:
        return False

    # Find the last path segment and its extension
    last_segment = path.rsplit("/", 1)[-1]
    # Extension is the part after the last dot
    dot_idx = last_segment.rfind(".")
    if dot_idx == -1:
        return False
    extension = last_segment[dot_idx:]
    return extension in _ASSET_EXTENSIONS
