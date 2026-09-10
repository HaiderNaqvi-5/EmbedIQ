"""Tests for the MarkdownChunker (app.services.chunker)."""

import hashlib
import textwrap

import pytest

from app.services.chunker import MarkdownChunker, Chunk, _estimate_tokens, _sha256

# ---------------------------------------------------------------------------
# Sample document with YAML frontmatter and multiple ## Page: sections
# ---------------------------------------------------------------------------

SAMPLE_WEBSITE_MD = textwrap.dedent("""\
    ---
    schema_version: "2.0"
    bot_id: "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    crawl_job_id: "11111111-2222-3333-4444-555555555555"
    website_url: "https://example.com"
    website_name: "Example Corp"
    crawled_at: "2025-01-15T12:00:00Z"
    total_pages_indexed: 2
    ---

    # Knowledge Base: Example Corp

    ## Page: Home
    - Source URL: https://example.com/
    - Title: Home

    Welcome to Example Corp. We build great things for great people.

    ## Page: Pricing
    - Source URL: https://example.com/pricing
    - Title: Pricing

    ### Enterprise Plan
    The Enterprise plan includes unlimited seats, dedicated support, and custom integrations.
    Perfect for large teams that need flexibility and scale.

    ### Starter Plan
    Our Starter plan is designed for small teams getting started with AI.
    Includes up to 5 users and 10,000 queries per month.

    ### Growth Plan
    The Growth plan scales with your business.
    Includes 25 users, 100,000 queries, and priority support.
""")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestMultiPageBoundary:
    """Chunks never merge content across different ## Page: sections."""

    def test_chunks_from_different_pages_are_separate(self):
        chunker = MarkdownChunker()
        chunks = chunker.chunk_document(SAMPLE_WEBSITE_MD)

        home_chunks = [c for c in chunks if c.page_title == "Home"]
        pricing_chunks = [c for c in chunks if c.page_title == "Pricing"]

        assert len(home_chunks) >= 1
        assert len(pricing_chunks) >= 1

        for hc in home_chunks:
            assert "Starter plan" not in hc.content
            assert "Enterprise plan" not in hc.content

        for pc in pricing_chunks:
            assert "build great things" not in pc.content


class TestHeadingPath:
    """Heading path reflects the heading hierarchy within a page."""

    def test_heading_path_construction(self):
        # A section longer than target_tokens (600) is flushed while still
        # under its own heading, so the emitted chunk carries that path.
        long_para = " ".join(["Enterprise"] * 470)  # ~611 tokens
        md = textwrap.dedent(f"""\
            ## Page: Pricing
            - Source URL: https://example.com/pricing
            - Title: Pricing

            ### Enterprise Plan
            {long_para}

            ### Starter Plan
            Short starter description that stays in its own section.
        """)

        chunker = MarkdownChunker()
        chunks = chunker.chunk_document(md)

        enterprise_chunks = [c for c in chunks if "Enterprise Plan" in c.heading_path]
        assert len(enterprise_chunks) >= 1
        for c in enterprise_chunks:
            assert c.heading_path == "Pricing > Enterprise Plan"

    def test_heading_path_with_sub_sections(self):
        # A #### heading nested under a ### heading produces a 3-level path,
        # e.g. "Pricing > Enterprise Plan > Features".
        long_para = " ".join(["Feature"] * 470)  # ~611 tokens
        md = textwrap.dedent(f"""\
            ## Page: Pricing
            - Source URL: https://example.com/pricing
            - Title: Pricing

            ### Enterprise Plan
            Short enterprise intro that won't trigger an early flush.

            #### Features
            {long_para}
        """)

        chunker = MarkdownChunker()
        chunks = chunker.chunk_document(md)

        feature_chunks = [c for c in chunks if "Features" in c.heading_path]
        assert len(feature_chunks) >= 1
        for c in feature_chunks:
            assert c.heading_path == "Pricing > Enterprise Plan > Features"

    def test_heading_path_uses_page_title_as_root(self):
        chunker = MarkdownChunker()
        chunks = chunker.chunk_document(SAMPLE_WEBSITE_MD)

        home_chunks = [c for c in chunks if c.page_title == "Home"]
        assert len(home_chunks) >= 1
        assert home_chunks[0].heading_path == "Home"


class TestTokenCount:
    """Token counts stay within the configured limits."""

    def test_all_chunks_within_max_tokens(self):
        chunker = MarkdownChunker(target_tokens=600, max_tokens=1000)
        chunks = chunker.chunk_document(SAMPLE_WEBSITE_MD)

        for chunk in chunks:
            assert chunk.token_count <= 1000, (
                f"Chunk exceeds max_tokens: {chunk.token_count}"
            )
            assert chunk.token_count >= 1

    def test_token_count_matches_estimate(self):
        chunker = MarkdownChunker()
        chunks = chunker.chunk_document(SAMPLE_WEBSITE_MD)

        for chunk in chunks:
            expected = _estimate_tokens(chunk.content)
            assert chunk.token_count == expected


class TestOversizedParagraphSplitting:
    """Oversized paragraphs are split into multiple chunks with overlap."""

    def test_oversized_paragraph_produces_multiple_chunks(self):
        long_paragraph = " ".join(["word"] * 1200)  # ~1560 tokens
        md = textwrap.dedent(f"""\
            ## Page: LongPage
            - Source URL: https://example.com/long
            - Title: LongPage

            {long_paragraph}
        """)

        chunker = MarkdownChunker(target_tokens=600, max_tokens=1000)
        chunks = chunker.chunk_document(md)

        assert len(chunks) > 1
        for c in chunks:
            assert c.token_count <= 1000

    def test_split_chunks_stay_within_page(self):
        long_paragraph = " ".join(["word"] * 1200)
        md = textwrap.dedent(f"""\
            ## Page: LongPage
            - Source URL: https://example.com/long
            - Title: LongPage

            {long_paragraph}
        """)

        chunker = MarkdownChunker()
        chunks = chunker.chunk_document(md)
        assert all(c.page_title == "LongPage" for c in chunks)


class TestEmptyAndShortDocuments:
    """Edge cases: empty content, frontmatter-only, single short page."""

    def test_empty_document(self):
        chunker = MarkdownChunker()
        chunks = chunker.chunk_document("")
        assert chunks == []

    def test_frontmatter_only(self):
        md = textwrap.dedent("""\
            ---
            schema_version: "2.0"
            bot_id: "test"
            ---
        """)
        chunker = MarkdownChunker()
        chunks = chunker.chunk_document(md)
        assert chunks == []

    def test_single_short_page(self):
        md = textwrap.dedent("""\
            ## Page: Tiny
            - Source URL: https://example.com/tiny
            - Title: Tiny

            Hello world.
        """)
        chunker = MarkdownChunker()
        chunks = chunker.chunk_document(md)
        assert len(chunks) == 1
        assert "Hello world" in chunks[0].content


class TestSequentialChunkIndex:
    """chunk_index is sequential across all pages."""

    def test_indices_are_zero_based_and_sequential(self):
        chunker = MarkdownChunker()
        chunks = chunker.chunk_document(SAMPLE_WEBSITE_MD)

        assert len(chunks) >= 2
        indices = [c.chunk_index for c in chunks]
        assert indices == list(range(len(chunks)))

    def test_indices_continue_across_pages(self):
        md = textwrap.dedent("""\
            ## Page: First
            - Source URL: https://example.com/first
            - Title: First

            Content for first page. Some extra text to make it real.

            ## Page: Second
            - Source URL: https://example.com/second
            - Title: Second

            Content for second page. More text to fill things out.
        """)
        chunker = MarkdownChunker()
        chunks = chunker.chunk_document(md)

        indices = [c.chunk_index for c in chunks]
        assert indices == list(range(len(chunks)))


class TestPageMetadata:
    """source_url and page_title are correctly extracted from page headers."""

    def test_source_url_from_page_header(self):
        chunker = MarkdownChunker()
        chunks = chunker.chunk_document(SAMPLE_WEBSITE_MD)

        home_chunks = [c for c in chunks if c.page_title == "Home"]
        assert all(c.source_url == "https://example.com/" for c in home_chunks)

        pricing_chunks = [c for c in chunks if c.page_title == "Pricing"]
        assert all(
            c.source_url == "https://example.com/pricing"
            for c in pricing_chunks
        )

    def test_page_title_matches_header(self):
        chunker = MarkdownChunker()
        chunks = chunker.chunk_document(SAMPLE_WEBSITE_MD)

        titles = {c.page_title for c in chunks}
        assert "Home" in titles
        assert "Pricing" in titles

    def test_content_hash_is_sha256(self):
        chunker = MarkdownChunker()
        chunks = chunker.chunk_document(SAMPLE_WEBSITE_MD)

        for chunk in chunks:
            expected = hashlib.sha256(
                chunk.content.encode("utf-8", errors="replace")
            ).hexdigest()
            assert chunk.content_hash == expected
            assert len(chunk.content_hash) == 64
