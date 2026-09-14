"""Tests for the RAG engine helpers (app.services.rag)."""

import pytest

from app.services.rag import (
    ChatMessage,
    RAGRequest,
    RAGResponse,
    _build_system_prompt,
    _deduplicate_sources,
    _format_chunks_xml,
    _trim_history,
    chat_with_rag,
)
from app.services.retrieval import RetrievedChunk


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_chunk(
    content: str = "test content",
    source_url: str = "https://example.com/page",
    page_title: str = "Page Title",
    heading_path: str = "Page Title > Section",
    similarity: float = 0.9,
) -> RetrievedChunk:
    return RetrievedChunk(
        id=None,
        source_url=source_url,
        page_title=page_title,
        heading_path=heading_path,
        content=content,
        similarity=similarity,
    )


# ---------------------------------------------------------------------------
# _format_chunks_xml
# ---------------------------------------------------------------------------


class TestFormatChunksXml:
    def test_single_chunk(self):
        chunk = _make_chunk(
            content="Hello world",
            source_url="https://a.com",
            page_title="Home",
        )
        result = _format_chunks_xml([chunk])

        assert '<chunk source="https://a.com" title="Home">' in result
        assert "Hello world" in result
        assert "</chunk>" in result

    def test_multiple_chunks(self):
        chunks = [
            _make_chunk(content="First", source_url="https://a.com", page_title="A"),
            _make_chunk(content="Second", source_url="https://b.com", page_title="B"),
        ]
        result = _format_chunks_xml(chunks)

        assert result.count("<chunk") == 2
        assert result.count("</chunk>") == 2
        assert "First" in result
        assert "Second" in result

    def test_empty_list(self):
        result = _format_chunks_xml([])
        assert result == ""


# ---------------------------------------------------------------------------
# _build_system_prompt
# ---------------------------------------------------------------------------


class TestBuildSystemPrompt:
    def test_contains_company_name(self):
        prompt = _build_system_prompt("Acme Corp", "<chunk></chunk>")
        assert "Acme Corp" in prompt

    def test_contains_context_usage_rules(self):
        prompt = _build_system_prompt("Test", "")
        assert "CONTEXT USAGE RULES" in prompt

    def test_contains_untrusted_data_warning(self):
        prompt = _build_system_prompt("Test", "")
        assert "untrusted reference data" in prompt

    def test_contains_website_context_tags(self):
        prompt = _build_system_prompt("Test", "<chunk>content</chunk>")
        assert "<website_context>" in prompt
        assert "</website_context>" in prompt

    def test_instructs_no_assumption(self):
        prompt = _build_system_prompt("Test", "")
        assert "Do NOT assume" in prompt.lower() or "NOT assume" in prompt


# ---------------------------------------------------------------------------
# _trim_history
# ---------------------------------------------------------------------------


class TestTrimHistory:
    def test_short_history_kept_intact(self):
        msgs = [ChatMessage(role="user", content=str(i)) for i in range(4)]
        result = _trim_history(msgs)

        assert len(result) == 4
        assert result[0]["role"] == "user"
        assert result[0]["content"] == "0"

    def test_long_history_trimmed_to_six(self):
        msgs = [ChatMessage(role="user", content=str(i)) for i in range(10)]
        result = _trim_history(msgs)

        assert len(result) == 6
        assert result[0]["content"] == "4"
        assert result[-1]["content"] == "9"

    def test_empty_history(self):
        result = _trim_history([])
        assert result == []


# ---------------------------------------------------------------------------
# _deduplicate_sources
# ---------------------------------------------------------------------------


class TestDeduplicateSources:
    def test_unique_urls(self):
        chunks = [
            _make_chunk(source_url="https://a.com", page_title="A"),
            _make_chunk(source_url="https://b.com", page_title="B"),
        ]
        sources = _deduplicate_sources(chunks)
        assert len(sources) == 2
        assert sources[0]["url"] == "https://a.com"
        assert sources[1]["url"] == "https://b.com"

    def test_duplicate_urls_collapsed(self):
        chunks = [
            _make_chunk(source_url="https://a.com", page_title="A"),
            _make_chunk(source_url="https://a.com", page_title="A"),
            _make_chunk(source_url="https://b.com", page_title="B"),
        ]
        sources = _deduplicate_sources(chunks)
        assert len(sources) == 2
        urls = [s["url"] for s in sources]
        assert urls == ["https://a.com", "https://b.com"]

    def test_preserves_first_title(self):
        chunks = [
            _make_chunk(source_url="https://a.com", page_title="First Title"),
            _make_chunk(source_url="https://a.com", page_title="Second Title"),
        ]
        sources = _deduplicate_sources(chunks)
        assert sources[0]["title"] == "First Title"

    def test_empty_input(self):
        assert _deduplicate_sources([]) == []


# ---------------------------------------------------------------------------
# chat_with_rag with 0 chunks (deterministic out-of-scope reply)
# ---------------------------------------------------------------------------


class TestChatWithRagZeroChunks:
    @pytest.mark.asyncio
    async def test_returns_out_of_scope_reply(self, monkeypatch):
        """When retrieval returns empty, the deterministic refusal is returned."""
        import app.services.rag as rag_mod

        async def _mock_retrieve(*args, **kwargs):
            return []

        async def _mock_persist(*args, **kwargs):
            pass

        async def _mock_get_or_create(*args, **kwargs):
            return None

        async def _mock_get_query_embedding(*args, **kwargs):
            return [0.0] * 1536

        monkeypatch.setattr(rag_mod, "retrieve_chunks", _mock_retrieve)
        monkeypatch.setattr(rag_mod, "_persist_turn", _mock_persist)
        monkeypatch.setattr(rag_mod, "_get_or_create_conversation", _mock_get_or_create)
        monkeypatch.setattr(rag_mod, "_get_query_embedding", _mock_get_query_embedding)

        rag_request = RAGRequest(
            bot_id=None,
            session_id="test-session",
            user_message="What is the meaning of life?",
            history=[],
            db=None,
            bot_name="Test Bot",
        )

        result = await chat_with_rag(rag_request)

        assert isinstance(result, RAGResponse)
        assert "don't have information" in result.answer.lower() or "sorry" in result.answer.lower()
        assert result.sources == []
        assert result.retrieved_chunks == 0
