"""
Bot-Scoped Vector Retrieval Service (PRD Section 6.3.1)
=======================================================
Performs cosine similarity search against the pgvector chunks table,
strictly scoped to a single bot_id. Cross-bot retrieval is architecturally
prohibited — every query MUST include a bot_id filter.
"""

import logging
import uuid
from dataclasses import dataclass
from typing import List

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings

logger = logging.getLogger("embediq.retrieval")


@dataclass
class RetrievedChunk:
    """A single chunk returned from the vector similarity search."""

    id: uuid.UUID
    source_url: str
    page_title: str
    heading_path: str
    content: str
    similarity: float


async def retrieve_chunks(
    bot_id: uuid.UUID,
    query_embedding: List[float],
    db: AsyncSession,
    top_k: int = None,
    min_similarity: float = None,
) -> List[RetrievedChunk]:
    """Bot-scoped cosine similarity search using pgvector.

    MANDATORY INVARIANT: always filters by bot_id. Never cross-bot retrieval.

    Args:
        bot_id: The UUID of the bot whose chunks to search. This filter is
                ALWAYS applied — no query can span multiple bots.
        query_embedding: The embedding vector for the user's query,
                         produced by the configured embedding provider.
        db: Active async database session.
        top_k: Maximum number of chunks to return. Defaults to
               settings.DEFAULT_TOP_K (8). Capped at settings.MAX_TOP_K (10).
        min_similarity: Minimum cosine similarity threshold (0-1). Chunks
                        with similarity below this value are discarded.
                        Defaults to settings.MIN_SIMILARITY_THRESHOLD (0.50).

    Returns:
        List of RetrievedChunk ordered by descending similarity (most relevant
        first). Returns an empty list when no chunks meet the threshold —
        the RAG engine interprets this as an out-of-scope query.
    """
    # Apply defaults from settings when not explicitly provided
    if top_k is None:
        top_k = settings.DEFAULT_TOP_K
    if min_similarity is None:
        min_similarity = settings.MIN_SIMILARITY_THRESHOLD

    # Clamp top_k to the configured maximum
    top_k = min(top_k, settings.MAX_TOP_K)

    # Serialize the embedding list to pgvector's text format: '[0.1,0.2,...]'
    vector_str = "[" + ",".join(str(v) for v in query_embedding) + "]"

    # PRD Section 6.3.1 — exact SQL contract. Uses the <=> cosine distance
    # operator provided by pgvector. The WHERE clause enforces bot isolation
    # at the query level so ORM-level mistakes cannot bypass it.
    # Pull a larger semantic candidate set first, then lightly re-rank it
    # based on generic page type. This prevents pages such as Terms/Privacy
    # from dominating broad product/service questions while still allowing
    # them to rank highly when the user's query is actually about those pages.
    #
    # IMPORTANT:
    # - similarity threshold is ALWAYS applied to raw cosine similarity
    # - bot_id isolation remains mandatory
    # - boosts/penalties are intentionally small so semantic relevance wins
    candidate_k = min(max(top_k * 4, top_k), 40)

    sql = text(
        """
        WITH candidates AS (
            SELECT id,
                   source_url,
                   page_title,
                   heading_path,
                   content,
                   1 - (embedding <=> :query_vector) AS similarity
            FROM chunks
            WHERE bot_id = :bot_id
              AND (1 - (embedding <=> :query_vector)) >= :min_similarity
            ORDER BY embedding <=> :query_vector ASC
            LIMIT :candidate_k
        ),
        ranked AS (
            SELECT *,
                   similarity
                   +
                   CASE
                       -- Service / solution pages are generally high-value
                       -- knowledge pages for customer questions.
                       WHEN LOWER(source_url) ~ '/(services?|solutions?)(/|$)'
                           THEN 0.050

                       -- Root/home pages often contain the broadest company
                       -- overview and are useful for general questions.
                       WHEN LOWER(source_url) ~ '^https?://[^/]+/?$'
                           THEN 0.030

                       -- Legal/supporting pages remain retrievable, but receive
                       -- a small penalty for unrelated broad questions.
                       WHEN LOWER(source_url) ~ '/(terms|privacy|cookies?|legal)(/|[-_?.#]|$)'
                           THEN -0.080

                       -- Galleries tend to contain weak textual knowledge.
                       WHEN LOWER(source_url) ~ '/gallery(/|[-_?.#]|$)'
                           THEN -0.060

                       ELSE 0.000
                   END AS retrieval_score
            FROM candidates
        )
        SELECT id,
               source_url,
               page_title,
               heading_path,
               content,
               similarity,
               retrieval_score
        FROM ranked
        ORDER BY retrieval_score DESC, similarity DESC
        LIMIT :top_k
        """
    )

    try:
        result = await db.execute(
            sql,
            {
                "query_vector": vector_str,
                "bot_id": str(bot_id),
                "min_similarity": min_similarity,
                "candidate_k": candidate_k,
                "top_k": top_k,
            },
        )
        rows = result.fetchall()
    except Exception as exc:
        logger.error(
            "Vector retrieval failed for bot_id=%s: %s", bot_id, exc, exc_info=True
        )
        raise

    chunks: List[RetrievedChunk] = []
    for row in rows:
        chunks.append(
            RetrievedChunk(
                id=row.id if isinstance(row.id, uuid.UUID) else uuid.UUID(str(row.id)),
                source_url=row.source_url or "",
                page_title=row.page_title or "",
                heading_path=row.heading_path or "",
                content=row.content or "",
                similarity=float(row.similarity),
            )
        )

    logger.info(
        "Retrieved %d chunk(s) for bot_id=%s (top_k=%d, candidate_k=%d, min_sim=%.2f)",
        len(chunks),
        bot_id,
        top_k,
        candidate_k,
        min_similarity,
    )

    for i, chunk in enumerate(chunks, start=1):
        preview = " ".join(chunk.content.split())[:500]
        logger.debug(
            "RAG RESULT #%d similarity=%.4f title=%r url=%s heading=%r preview=%r",
            i,
            chunk.similarity,
            chunk.page_title,
            chunk.source_url,
            chunk.heading_path,
            preview,
        )

    return chunks
