"""Tests for the embedding service (app.services.embedding_service)."""

import pytest

from app.services.embedding_service import (
    BaseEmbeddingProvider,
    MockEmbeddingProvider,
    embed_chunks_batch,
    get_embedding_provider,
)


# ---------------------------------------------------------------------------
# MockEmbeddingProvider
# ---------------------------------------------------------------------------


class TestMockEmbeddingProvider:
    @pytest.mark.asyncio
    async def test_returns_zero_vectors_of_correct_dimension(self):
        provider = MockEmbeddingProvider()
        texts = ["hello", "world", "test"]

        results = await provider.embed_texts(texts)

        assert len(results) == 3
        for vec in results:
            assert len(vec) == 1536
            assert all(v == 0.0 for v in vec)

    @pytest.mark.asyncio
    async def test_empty_input(self):
        provider = MockEmbeddingProvider()
        results = await provider.embed_texts([])
        assert results == []


# ---------------------------------------------------------------------------
# get_embedding_provider factory
# ---------------------------------------------------------------------------


class TestGetEmbeddingProvider:
    @pytest.mark.asyncio
    async def test_mock_provider_when_api_key_is_placeholder(self, monkeypatch):
        from app.core import config as config_mod

        monkeypatch.setattr(config_mod.settings, "EMBEDDING_API_KEY", "mock-key")
        monkeypatch.setattr(config_mod.settings, "EMBEDDING_PROVIDER", "openai")

        provider = get_embedding_provider()
        assert isinstance(provider, MockEmbeddingProvider)

    @pytest.mark.asyncio
    async def test_mock_provider_when_provider_not_openai(self, monkeypatch):
        from app.core import config as config_mod

        monkeypatch.setattr(config_mod.settings, "EMBEDDING_API_KEY", "sk-real-key")
        monkeypatch.setattr(config_mod.settings, "EMBEDDING_PROVIDER", "azure")

        provider = get_embedding_provider()
        assert isinstance(provider, MockEmbeddingProvider)


# ---------------------------------------------------------------------------
# embed_chunks_batch
# ---------------------------------------------------------------------------


class TestEmbedChunksBatch:
    @pytest.mark.asyncio
    async def test_processes_texts_in_correct_batch_sizes(self):
        call_counts = []

        class RecordingProvider(BaseEmbeddingProvider):
            async def embed_texts(self, texts):
                call_counts.append(len(texts))
                return [[0.0] * 1536 for _ in texts]

        texts = [f"text_{i}" for i in range(250)]
        results = await embed_chunks_batch(texts, provider=RecordingProvider(), batch_size=100)

        assert len(results) == 250
        assert call_counts == [100, 100, 50]

    @pytest.mark.asyncio
    async def test_handles_empty_input(self):
        provider = MockEmbeddingProvider()
        results = await embed_chunks_batch([], provider=provider)
        assert results == []

    @pytest.mark.asyncio
    async def test_single_batch(self):
        provider = MockEmbeddingProvider()
        texts = ["a", "b", "c"]
        results = await embed_chunks_batch(texts, provider=provider, batch_size=100)

        assert len(results) == 3
        for vec in results:
            assert len(vec) == 1536
