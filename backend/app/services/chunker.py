"""
Markdown-Aware Semantic Chunker (PRD Section 6.2.2)
====================================================
Splits a canonical website.md document into semantically coherent chunks
for embedding and vector storage. Strict invariants enforced:

  - Page boundaries (## Page:) are NEVER merged across chunks.
  - Target: ~600 tokens, Max: 1000 tokens, Overlap: 100 tokens on splits.
  - Token count uses a fast word-based approximation (words * 1.3).
"""

import hashlib
import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Chunk:
    """A single semantic chunk ready for embedding."""

    content: str
    heading_path: str          # e.g. "Pricing > Enterprise Plan"
    source_url: str
    page_title: str
    token_count: int
    content_hash: str          # SHA-256 of content
    chunk_index: int           # 0-based sequential index across entire document


# ---------------------------------------------------------------------------
# Token count approximation (no external dependency)
# ---------------------------------------------------------------------------

def _estimate_tokens(text: str) -> int:
    """Fast approximation: words × 1.3 (covers subword tokenization overhead)."""
    return max(1, int(len(text.split()) * 1.3))


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


# ---------------------------------------------------------------------------
# Markdown parser helpers
# ---------------------------------------------------------------------------

# Matches ## Page: … lines (page section headers)
_PAGE_RE = re.compile(r"^##\s+Page:\s*(.*)", re.MULTILINE)

# Matches ### or #### heading lines
_HEADING_RE = re.compile(r"^(#{3,6})\s+(.*)", re.MULTILINE)

# Matches the YAML frontmatter block
_FRONTMATTER_RE = re.compile(r"^---\n.*?\n---\n", re.DOTALL)

# Parses "- Source URL: …" lines inside page headers
_SOURCE_URL_RE = re.compile(r"^-\s+Source URL:\s+(.*)", re.MULTILINE)


def _extract_page_meta(page_block: str) -> dict:
    """Pull source_url from the page block header lines."""
    url_match = _SOURCE_URL_RE.search(page_block)
    return {
        "source_url": url_match.group(1).strip() if url_match else "",
    }


# ---------------------------------------------------------------------------
# Main chunker
# ---------------------------------------------------------------------------


class MarkdownChunker:
    """Markdown-aware chunker that respects page and heading boundaries."""

    def __init__(
        self,
        target_tokens: int = 600,
        max_tokens: int = 1000,
        overlap_tokens: int = 100,
    ):
        self.target_tokens = target_tokens
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def chunk_document(self, markdown_content: str) -> List[Chunk]:
        """Split a website.md document into semantic chunks.

        Algorithm:
        1. Strip frontmatter.
        2. Split on ## Page: boundaries.
        3. Within each page, split on ### / #### sub-headings.
        4. Within each sub-section, split on paragraphs if oversized.
        5. Never merge content across page boundaries.

        Returns:
            Ordered list of Chunk objects with sequential chunk_index.
        """
        # Strip YAML frontmatter
        body = _FRONTMATTER_RE.sub("", markdown_content).strip()

        # Split into page blocks on "## Page:" markers
        # We use re.split with a capturing group to preserve the delimiter
        parts = re.split(r"(^## Page:.*$)", body, flags=re.MULTILINE)

        # Reconstruct page blocks: the split gives alternating [pre, header, content, header, ...]
        pages: List[tuple] = []  # (page_title, full_block_text)
        i = 0
        # Skip any text before the first page header
        while i < len(parts) and not parts[i].startswith("## Page:"):
            i += 1

        while i < len(parts):
            header = parts[i]  # "## Page: Title"
            page_title = header.replace("## Page:", "").strip()
            content = parts[i + 1] if (i + 1) < len(parts) else ""
            pages.append((page_title, header + "\n" + content))
            i += 2

        all_chunks: List[Chunk] = []
        chunk_index = 0

        for page_title, page_block in pages:
            meta = _extract_page_meta(page_block)
            source_url = meta["source_url"]

            page_chunks = self._chunk_page(
                page_block=page_block,
                page_title=page_title,
                source_url=source_url,
                start_index=chunk_index,
            )
            all_chunks.extend(page_chunks)
            chunk_index += len(page_chunks)

        return all_chunks

    # ------------------------------------------------------------------
    # Per-page processing
    # ------------------------------------------------------------------

    def _chunk_page(
        self,
        page_block: str,
        page_title: str,
        source_url: str,
        start_index: int,
    ) -> List[Chunk]:
        """Split a single page block into chunks, respecting headings."""
        # Split page block on sub-headings (### and ####)
        sections = self._split_on_headings(page_block)

        chunks: List[Chunk] = []
        chunk_index = start_index
        heading_stack: List[str] = [page_title]

        buffer_lines: List[str] = []
        buffer_tokens: int = 0
        current_heading_path: str = page_title

        def flush(heading_path: str) -> None:
            nonlocal buffer_lines, buffer_tokens, chunk_index
            content = "\n".join(buffer_lines).strip()
            if not content:
                return
            c = self._make_chunk(
                content=content,
                heading_path=heading_path,
                source_url=source_url,
                page_title=page_title,
                index=chunk_index,
            )
            chunks.append(c)
            chunk_index += 1
            buffer_lines = []
            buffer_tokens = 0

        for section_heading, section_text in sections:
            if section_heading:
                # Update heading path
                heading_depth = len(re.match(r"^(#+)", section_heading).group(1))
                heading_label = re.sub(r"^#+\s*", "", section_heading).strip()

                # Maintain stack up to the current depth
                # h3 = depth 3 → index 1 in path (after page_title at 0)
                relative_depth = heading_depth - 2  # ## Page = depth 2
                if relative_depth > 0:
                    heading_stack = heading_stack[:relative_depth]
                    heading_stack.append(heading_label)
                current_heading_path = " > ".join(heading_stack)

                # If buffer has content and we hit a new heading, flush
                if buffer_lines and buffer_tokens > self.target_tokens // 2:
                    flush(current_heading_path)

            # Process lines in the section
            paragraphs = self._split_paragraphs(section_text)
            for para in paragraphs:
                para_tokens = _estimate_tokens(para)

                # If adding this paragraph exceeds max, flush first
                if buffer_tokens + para_tokens > self.max_tokens and buffer_lines:
                    # Apply overlap: keep last overlap_tokens worth of content
                    overlap_text = self._extract_overlap(buffer_lines)
                    flush(current_heading_path)
                    if overlap_text:
                        buffer_lines = [overlap_text]
                        buffer_tokens = _estimate_tokens(overlap_text)

                # If single paragraph exceeds max, split it
                if para_tokens > self.max_tokens:
                    sub_chunks = self._split_oversized(para, current_heading_path, source_url, page_title, chunk_index)
                    chunks.extend(sub_chunks)
                    chunk_index += len(sub_chunks)
                    continue

                buffer_lines.append(para)
                buffer_tokens += para_tokens

                if buffer_tokens >= self.target_tokens:
                    flush(current_heading_path)

        # Flush remaining buffer
        flush(current_heading_path)
        return chunks

    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------

    def _split_on_headings(self, text: str) -> List[tuple]:
        """Split text into (heading_line, section_text) pairs.

        The first tuple may have an empty heading (for content before any heading).
        """
        lines = text.split("\n")
        sections: List[tuple] = []
        current_heading = ""
        current_lines: List[str] = []

        for line in lines:
            if _HEADING_RE.match(line):
                sections.append((current_heading, "\n".join(current_lines)))
                current_heading = line
                current_lines = []
            else:
                current_lines.append(line)

        sections.append((current_heading, "\n".join(current_lines)))
        return sections

    def _split_paragraphs(self, text: str) -> List[str]:
        """Split text on blank lines to get paragraph units."""
        paragraphs = re.split(r"\n\s*\n", text)
        return [p.strip() for p in paragraphs if p.strip()]

    def _extract_overlap(self, buffer_lines: List[str]) -> str:
        """Extract the last overlap_tokens worth of text from the buffer."""
        if not buffer_lines:
            return ""
        # Take last few lines as overlap
        overlap_parts: List[str] = []
        token_count = 0
        for line in reversed(buffer_lines):
            line_tokens = _estimate_tokens(line)
            if token_count + line_tokens > self.overlap_tokens:
                break
            overlap_parts.insert(0, line)
            token_count += line_tokens
        return "\n".join(overlap_parts)

    def _split_oversized(
        self,
        text: str,
        heading_path: str,
        source_url: str,
        page_title: str,
        start_index: int,
    ) -> List["Chunk"]:
        """Split an oversized paragraph into max_tokens sized chunks with overlap."""
        words = text.split()
        chunks: List[Chunk] = []
        chunk_index = start_index

        # Approximate words per chunk
        target_words = int(self.target_tokens / 1.3)
        overlap_words = int(self.overlap_tokens / 1.3)

        i = 0
        while i < len(words):
            end = min(i + target_words, len(words))
            chunk_text = " ".join(words[i:end])
            chunks.append(
                self._make_chunk(chunk_text, heading_path, source_url, page_title, chunk_index)
            )
            chunk_index += 1
            i = end - overlap_words if end < len(words) else end

        return chunks

    def _make_chunk(
        self,
        content: str,
        heading_path: str,
        source_url: str,
        page_title: str,
        index: int,
    ) -> "Chunk":
        return Chunk(
            content=content,
            heading_path=heading_path,
            source_url=source_url,
            page_title=page_title,
            token_count=_estimate_tokens(content),
            content_hash=_sha256(content),
            chunk_index=index,
        )
