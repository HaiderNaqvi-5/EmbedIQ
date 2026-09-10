"""Tests for the canonical website.md builder (app.services.knowledge_builder)."""

import hashlib
import re

from app.services.knowledge_builder import PageData, build_website_md, _content_hash


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_page(
    url: str = "https://example.com/page",
    title: str = "Test Page",
    clean_text: str = "Test content for the page.",
    structured_data: dict = None,
) -> PageData:
    return PageData(
        url=url,
        title=title,
        clean_text=clean_text,
        structured_data=structured_data or {},
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestYAMLFrontmatter:
    def test_contains_bot_id(self):
        result = build_website_md(
            bot_id="bot-123",
            crawl_job_id="job-456",
            website_url="https://example.com",
            website_name="Example",
            pages=[],
        )
        assert 'bot_id: "bot-123"' in result

    def test_contains_crawl_job_id(self):
        result = build_website_md(
            bot_id="b", crawl_job_id="cj-789",
            website_url="https://x.com", website_name="X",
            pages=[],
        )
        assert 'crawl_job_id: "cj-789"' in result

    def test_contains_website_url(self):
        result = build_website_md(
            bot_id="b", crawl_job_id="c",
            website_url="https://mysite.com", website_name="My Site",
            pages=[],
        )
        assert 'website_url: "https://mysite.com"' in result

    def test_contains_website_name(self):
        result = build_website_md(
            bot_id="b", crawl_job_id="c",
            website_url="https://x.com", website_name="Acme Corp",
            pages=[],
        )
        assert 'website_name: "Acme Corp"' in result

    def test_contains_timestamps(self):
        result = build_website_md(
            bot_id="b", crawl_job_id="c",
            website_url="https://x.com", website_name="X",
            pages=[],
        )
        assert "crawled_at:" in result

    def test_frontmatter_delimited(self):
        result = build_website_md(
            bot_id="b", crawl_job_id="c",
            website_url="https://x.com", website_name="X",
            pages=[],
        )
        lines = result.split("\n")
        assert lines[0] == "---"
        end_fm = lines.index("---", 1)
        assert end_fm > 0


class TestPageSections:
    def test_per_page_headers(self):
        pages = [
            _make_page(url="https://a.com", title="Alpha"),
            _make_page(url="https://b.com", title="Beta"),
        ]
        result = build_website_md(
            bot_id="b", crawl_job_id="c",
            website_url="https://x.com", website_name="X",
            pages=pages,
        )
        assert "## Page: Alpha" in result
        assert "## Page: Beta" in result

    def test_source_url_in_section(self):
        page = _make_page(url="https://example.com/pricing", title="Pricing")
        result = build_website_md(
            bot_id="b", crawl_job_id="c",
            website_url="https://x.com", website_name="X",
            pages=[page],
        )
        assert "- Source URL: https://example.com/pricing" in result

    def test_title_in_section(self):
        page = _make_page(title="About Us")
        result = build_website_md(
            bot_id="b", crawl_job_id="c",
            website_url="https://x.com", website_name="X",
            pages=[page],
        )
        assert "- Title: About Us" in result

    def test_content_hash_present(self):
        page = _make_page(clean_text="Some content here")
        result = build_website_md(
            bot_id="b", crawl_job_id="c",
            website_url="https://x.com", website_name="X",
            pages=[page],
        )
        expected_hash = _content_hash("Some content here")
        assert f"- Content Hash: {expected_hash}" in result


class TestContentHash:
    def test_hash_is_16_hex_chars(self):
        h = _content_hash("test data")
        assert len(h) == 16
        assert all(c in "0123456789abcdef" for c in h)

    def test_hash_deterministic(self):
        assert _content_hash("same input") == _content_hash("same input")

    def test_hash_differs_for_different_input(self):
        assert _content_hash("alpha") != _content_hash("beta")


class TestEmptyPages:
    def test_valid_document_with_no_pages(self):
        result = build_website_md(
            bot_id="b", crawl_job_id="c",
            website_url="https://x.com", website_name="X",
            pages=[],
        )
        assert result.startswith("---")
        assert "total_pages_indexed: 0" in result

    def test_total_pages_indexed_matches(self):
        pages = [_make_page(), _make_page(), _make_page()]
        result = build_website_md(
            bot_id="b", crawl_job_id="c",
            website_url="https://x.com", website_name="X",
            pages=pages,
        )
        assert "total_pages_indexed: 3" in result


class TestMultiplePages:
    def test_multiple_pages_produce_multiple_sections(self):
        pages = [
            _make_page(title="P1", url="https://x.com/p1", clean_text="Content 1"),
            _make_page(title="P2", url="https://x.com/p2", clean_text="Content 2"),
            _make_page(title="P3", url="https://x.com/p3", clean_text="Content 3"),
        ]
        result = build_website_md(
            bot_id="b", crawl_job_id="c",
            website_url="https://x.com", website_name="X",
            pages=pages,
        )
        assert result.count("## Page:") == 3
        assert "Content 1" in result
        assert "Content 2" in result
        assert "Content 3" in result
