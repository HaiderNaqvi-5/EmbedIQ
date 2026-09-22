"""
Jina embedding service for EmbedIQ.

Default model:
    jina-embeddings-v5-text-small

The hosted Jina v5 text model emits 1024-dimensional vectors. This service
keeps compatibility with the existing pgvector Vector(1536) schema by padding
each 1024-dimensional embedding with zeros up to settings.EMBEDDING_DIMENSION.

Zero-padding preserves cosine similarity when applied consistently to both
document and query vectors.

Public API:
    - get_embedding_provider()
    - embed_chunks_batch(texts)
    - provider.embed_texts(texts, task="retrieval.passage")
    - provider.embed_query(text)
"""

from __future__ import annotations

import asyncio
import logging
import os
from abc import ABC, abstractmethod
from typing import List, Sequence

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

JINA_API_URL = "https://api.jina.ai/v1/embeddings"
JINA_NATIVE_DIMENSION = 1024
DEFAULT_BATCH_SIZE = 64
HTTP_TIMEOUT_SECONDS = 60.0
MAX_RETRIES = 3


class BaseEmbeddingProvider(ABC):
    """Small provider contract used by ingestion and deterministic tests."""

    @abstractmethod
    async def embed_texts(self, texts: Sequence[str]) -> List[List[float]]:
        """Return one configured-dimension vector for each supplied text."""

    async def embed_query(self, text: str) -> List[float]:
        """Embed one retrieval query using the provider's default text mode."""
        vectors = await self.embed_texts([text])
        if not vectors:
            raise RuntimeError("Embedding provider returned no query embedding.")
        return vectors[0]


class MockEmbeddingProvider(BaseEmbeddingProvider):
    """Offline provider for local development when credentials are placeholders."""

    async def embed_texts(self, texts: Sequence[str]) -> List[List[float]]:
        return [[0.0] * int(settings.EMBEDDING_DIMENSION) for _ in texts]


def _fit_dimension(vector: Sequence[float]) -> List[float]:
    """Pad Jina vectors to the configured pgvector dimension when needed."""
    values = [float(v) for v in vector]
    target = int(settings.EMBEDDING_DIMENSION)

    if len(values) == target:
        return values

    if len(values) < target:
        return values + [0.0] * (target - len(values))

    raise RuntimeError(
        f"Jina returned {len(values)} dimensions but "
        f"EMBEDDING_DIMENSION={target}. Refusing to truncate vectors."
    )


class JinaEmbeddingProvider(BaseEmbeddingProvider):
    """Jina AI embedding provider for retrieval workloads."""

    def __init__(self) -> None:
        self.model = settings.EMBEDDING_MODEL or "jina-embeddings-v5-text-small"
        self.api_key = os.getenv("JINA_API_KEY") or getattr(
            settings, "JINA_API_KEY", None
        )

        if not self.api_key:
            raise RuntimeError(
                "JINA_API_KEY is missing. Add it to the project .env file."
            )

    async def _request(
        self,
        texts: Sequence[str],
        task: str,
    ) -> List[List[float]]:
        payload = {
            "model": self.model,
            "task": task,
            "dimensions": JINA_NATIVE_DIMENSION,
            "normalized": True,
            "embedding_type": "float",
            "input": list(texts),
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        last_error: Exception | None = None

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                async with httpx.AsyncClient(
                    timeout=HTTP_TIMEOUT_SECONDS
                ) as client:
                    response = await client.post(
                        JINA_API_URL,
                        headers=headers,
                        json=payload,
                    )

                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After")
                    delay = float(retry_after) if retry_after else (2 ** attempt)
                    logger.warning(
                        "Jina rate limit hit; retrying in %.1fs (%d/%d)",
                        delay,
                        attempt,
                        MAX_RETRIES,
                    )
                    await asyncio.sleep(delay)
                    continue

                response.raise_for_status()
                body = response.json()

                data = sorted(
                    body.get("data", []),
                    key=lambda item: item.get("index", 0),
                )

                if len(data) != len(texts):
                    raise RuntimeError(
                        "Jina returned an unexpected number of embeddings: "
                        f"expected={len(texts)} got={len(data)}"
                    )

                vectors = [
                    _fit_dimension(item["embedding"])
                    for item in data
                ]

                logger.info(
                    "Embedded %d text(s) with Jina model=%s task=%s "
                    "native_dimension=%d configured_dimension=%d",
                    len(vectors),
                    self.model,
                    task,
                    JINA_NATIVE_DIMENSION,
                    settings.EMBEDDING_DIMENSION,
                )

                return vectors

            except (httpx.HTTPError, RuntimeError, KeyError, ValueError) as exc:
                last_error = exc

                if attempt >= MAX_RETRIES:
                    break

                delay = 2 ** attempt
                logger.warning(
                    "Jina embedding request failed; retrying in %ds (%d/%d): %s",
                    delay,
                    attempt,
                    MAX_RETRIES,
                    exc,
                )
                await asyncio.sleep(delay)

        raise RuntimeError(
            f"Jina embedding failed after {MAX_RETRIES} attempts: {last_error}"
        )

    async def embed_texts(
        self,
        texts: Sequence[str],
        task: str = "retrieval.passage",
    ) -> List[List[float]]:
        """Embed document passages or explicitly requested task type."""
        if not texts:
            return []

        clean_texts = [str(text or "").strip() for text in texts]

        if any(not text for text in clean_texts):
            raise ValueError("Cannot embed empty text.")

        if task not in {"retrieval.passage", "retrieval.query"}:
            raise ValueError(
                f"Unsupported Jina task={task!r}; expected "
                "'retrieval.passage' or 'retrieval.query'."
            )

        return await self._request(clean_texts, task)

    async def embed_query(self, text: str) -> List[float]:
        """Embed one RAG/search query with Jina's retrieval.query task."""
        vectors = await self.embed_texts(
            [text],
            task="retrieval.query",
        )
        return vectors[0]


_PROVIDER: BaseEmbeddingProvider | None = None


def get_embedding_provider() -> BaseEmbeddingProvider:
    """Return the configured provider, retaining an offline safe development mode."""
    global _PROVIDER

    provider_name = (settings.EMBEDDING_PROVIDER or "jina").strip().lower()
    configured_key = getattr(settings, "JINA_API_KEY", None) or getattr(settings, "EMBEDDING_API_KEY", None)

    if _PROVIDER is None:
        # Placeholder credentials and non-Jina legacy settings must keep local
        # workflows testable without attempting a network call.
        _PROVIDER = (
            MockEmbeddingProvider()
            if configured_key in {None, "", "mock-key"} or provider_name != "jina"
            else JinaEmbeddingProvider()
        )

    return _PROVIDER


async def embed_chunks_batch(
    texts: Sequence[str],
    provider: BaseEmbeddingProvider | None = None,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> List[List[float]]:
    """Embed crawled chunks as Jina retrieval passages."""
    if not texts:
        return []

    active_provider = provider or get_embedding_provider()
    all_embeddings: List[List[float]] = []

    for start in range(0, len(texts), batch_size):
        batch = texts[start : start + batch_size]

        batch_embeddings = await active_provider.embed_texts(batch)
        all_embeddings.extend(batch_embeddings)

        logger.info(
            "Jina embedding progress: %d/%d chunks",
            min(start + len(batch), len(texts)),
            len(texts),
        )

    return all_embeddings
