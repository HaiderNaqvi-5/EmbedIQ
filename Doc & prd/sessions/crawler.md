# Session: Website Intelligence Engine (Milestone 3)

## Status: COMPLETE

## Date
2026-09-09

## Summary
Implemented the full 4-layer website intelligence engine: SSRF guard, URL normalizer, content extractor, and async crawler with Playwright fallback.

## Files Created

### Services
- `backend/app/services/__init__.py` — Package init
- `backend/app/services/ssrf_guard.py` — SSRF protection layer
- `backend/app/services/url_normalizer.py` — URL normalization utilities
- `backend/app/services/extractor.py` — HTML content extraction + branding heuristics
- `backend/app/services/crawler.py` — Full async crawler with BFS discovery

## Architecture

### SSRF Guard (`ssrf_guard.py`)
- Protocol whitelist: http, https only
- DNS pre-resolution via `socket.getaddrinfo()`
- CIDR blacklist: loopback, RFC1918, link-local, cloud metadata
- Credential rejection (user:pass@host)
- Blocked hostname suffix rejection (.internal, .local, .cluster.local)

### URL Normalizer (`url_normalizer.py`)
- Strips tracking params (utm_*, fbclid, gclid, ref, mc_eid, _ga)
- Strips #fragment
- Origin extraction
- Same-origin detection (with www. variant handling)
- Asset URL detection (.jpg, .pdf, .css, etc.)

### Content Extractor (`extractor.py`)
- Removes noise: script, style, noscript, nav, footer, header, aside
- Removes cookie consent dialogs by CSS class patterns
- Extracts: title, meta description, headings (h1-h6), paragraphs, tables
- Branding extraction: company name, logo URL, favicon, primary color
- Confidence scoring for each extracted branding field

### Crawler (`crawler.py`)
- BFS page discovery with robots.txt + sitemap.xml support
- Concurrency controlled via asyncio.Semaphore
- HTTPX for fast HTTP fetching
- Playwright fallback triggered by: text < 200 chars, SPA indicators
- Per PRD: max 50 pages, max depth 4, max 5 redirects, 5 concurrent

## PRD Invariants Verified
- Every URL validated through SSRF guard before network access
- Redirect destinations re-validated through SSRF guard
- User-Agent: 'EmbedIQ-Crawler/2.0 (+https://embediq.io/bot)'
- Max pages: MAX_PAGES_PER_BOT (50)
- Max depth: MAX_CRAWL_DEPTH (4)
