"""
Canonical website.md Builder (PRD Section 6.2.1)
================================================
Compiles crawled pages into a single deterministic Markdown artifact
with YAML frontmatter and structured per-page sections.
"""

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class PageData:
    """Minimal page data needed to build a knowledge entry."""

    url: str
    title: str
    clean_text: str
    structured_data: Dict[str, Any] = field(default_factory=dict)


def _content_hash(text: str) -> str:
    """Return first 16 hex chars of SHA-256 hash of text."""
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:16]


def _render_page_section(page: PageData, index: int) -> str:
    """Render a single page as a Markdown section.

    Format (per PRD Section 6.2.1):

        ## Page: {title}
        - Source URL: {url}
        - Title: {title}
        - Content Hash: {hash}

        ### {heading}
        {paragraph text}
        ...

        ---
    """
    lines: List[str] = []

    title = (page.title or "Untitled Page").strip()
    lines.append(f"## Page: {title}")
    lines.append(f"- Source URL: {page.url}")
    lines.append(f"- Title: {title}")
    lines.append(f"- Content Hash: {_content_hash(page.clean_text)}")
    lines.append("")

    # Emit structured headings and paragraphs when available
    sd = page.structured_data or {}
    headings: List[Dict] = sd.get("headings", [])
    paragraphs: List[str] = sd.get("paragraphs", [])
    tables: List[str] = sd.get("tables", [])

    if headings:
        for h in headings:
            level = h.get("level", "h2")
            text = h.get("text", "").strip()
            if not text:
                continue
            md_level = "#" * (int(level.replace("h", "")) + 1)  # h1→##, h2→###
            lines.append(f"{md_level} {text}")
            lines.append("")

    if paragraphs:
        for para in paragraphs:
            stripped = para.strip()
            if stripped:
                lines.append(stripped)
                lines.append("")
    elif not headings:
        # Fallback: dump clean_text directly
        if page.clean_text.strip():
            lines.append(page.clean_text.strip())
            lines.append("")

    for table in tables:
        if table.strip():
            lines.append(table.strip())
            lines.append("")

    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def build_website_md(
    bot_id: str,
    crawl_job_id: str,
    website_url: str,
    website_name: str,
    pages: List[PageData],
    failed_pages: int = 0,
) -> str:
    """Build the canonical website.md document.

    Args:
        bot_id: UUID string of the bot.
        crawl_job_id: UUID string of the crawl job.
        website_url: Root URL of the crawled website.
        website_name: Human-readable site/company name.
        pages: List of successfully crawled and extracted pages.
        failed_pages: Count of pages that failed to crawl.

    Returns:
        A string containing the full canonical Markdown document.
    """
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # ── YAML frontmatter ────────────────────────────────────────────────────
    frontmatter_lines = [
        "---",
        'schema_version: "2.0"',
        f'bot_id: "{bot_id}"',
        f'crawl_job_id: "{crawl_job_id}"',
        f'website_url: "{website_url}"',
        f'website_name: "{website_name}"',
        f'crawled_at: "{now_iso}"',
        f"total_pages_indexed: {len(pages)}",
        f"failed_pages: {failed_pages}",
        "---",
        "",
        f"# Knowledge Base: {website_name}",
        "",
    ]
    header = "\n".join(frontmatter_lines)

    # ── Per-page sections ────────────────────────────────────────────────────
    page_sections: List[str] = []
    for i, page in enumerate(pages):
        page_sections.append(_render_page_section(page, i))

    return header + "\n".join(page_sections)
