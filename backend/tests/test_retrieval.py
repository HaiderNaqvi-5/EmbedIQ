"""Tests for bot-scoped vector retrieval (app.services.retrieval)."""

import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.retrieval import retrieve_chunks, RetrievedChunk


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _vector_str(values: list[float]) -> str:
    """Serialize a list of floats to pgvector text format."""
    return "[" + ",".join(str(v) for v in values) + "]"


async def _insert_user(db: AsyncSession) -> uuid.UUID:
    user_id = uuid.uuid4()
    await db.execute(
        text(
            "INSERT INTO users (id, email, password_hash, is_active, created_at, updated_at) "
            "VALUES (:id, :email, :pw, true, now(), now())"
        ),
        {"id": str(user_id), "email": f"test-{user_id.hex[:8]}@example.com", "pw": "hash"},
    )
    return user_id


async def _insert_bot(db: AsyncSession, user_id: uuid.UUID) -> uuid.UUID:
    bot_id = uuid.uuid4()
    await db.execute(
        text(
            "INSERT INTO bots (id, user_id, name, website_url, normalized_origin, status, created_at, updated_at) "
            "VALUES (:id, :uid, :name, :url, :origin, 'READY', now(), now())"
        ),
        {"id": str(bot_id), "uid": str(user_id), "name": "TestBot", "url": "https://example.com", "origin": "https://example.com"},
    )
    return bot_id


async def _insert_crawl_job(db: AsyncSession, bot_id: uuid.UUID) -> uuid.UUID:
    job_id = uuid.uuid4()
    await db.execute(
        text(
            "INSERT INTO crawl_jobs (id, bot_id, status, stage, total_pages, processed_pages, failed_pages, warning_count, created_at) "
            "VALUES (:id, :bot, 'COMPLETED', 'COMPLETED', 1, 1, 0, 0, now())"
        ),
        {"id": str(job_id), "bot": str(bot_id)},
    )
    return job_id


async def _insert_document(db: AsyncSession, bot_id: uuid.UUID, crawl_job_id: uuid.UUID) -> uuid.UUID:
    doc_id = uuid.uuid4()
    await db.execute(
        text(
            "INSERT INTO documents (id, bot_id, crawl_job_id, type, content, content_hash, created_at) "
            "VALUES (:id, :bot, :job, 'CANONICAL_MARKDOWN', 'test', 'hash123', now())"
        ),
        {"id": str(doc_id), "bot": str(bot_id), "job": str(crawl_job_id)},
    )
    return doc_id


async def _insert_chunk(
    db: AsyncSession,
    bot_id: uuid.UUID,
    document_id: uuid.UUID,
    embedding: list[float],
    content: str = "chunk content",
    source_url: str = "https://example.com",
    page_title: str = "Test Page",
    heading_path: str = "Test Page",
    chunk_index: int = 0,
) -> uuid.UUID:
    chunk_id = uuid.uuid4()
    await db.execute(
        text(
            "INSERT INTO chunks "
            "(id, bot_id, document_id, source_url, page_title, heading_path, content, content_hash, chunk_index, token_count, embedding, metadata, created_at) "
            "VALUES (:id, :bot, :doc, :url, :title, :heading, :content, :chash, :cidx, :tok, :emb, '{}'::jsonb, now())"
        ),
        {
            "id": str(chunk_id),
            "bot": str(bot_id),
            "doc": str(document_id),
            "url": source_url,
            "title": page_title,
            "heading": heading_path,
            "content": content,
            "chash": "abc123",
            "cidx": chunk_index,
            "tok": 10,
            "emb": _vector_str(embedding),
        },
    )
    return chunk_id


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_bot_scoped_filtering(db_session: AsyncSession):
    """Chunks from bot A are returned; chunks from bot B are excluded."""
    user_id = await _insert_user(db_session)
    bot_a = await _insert_bot(db_session, user_id)
    job_a = await _insert_crawl_job(db_session, bot_a)
    doc_a = await _insert_document(db_session, bot_a, job_a)

    bot_b = await _insert_bot(db_session, user_id)
    job_b = await _insert_crawl_job(db_session, bot_b)
    doc_b = await _insert_document(db_session, bot_b, job_b)

    embedding_a = [1.0] + [0.0] * 1535
    embedding_b = [0.0] * 1536

    await _insert_chunk(db_session, bot_a, doc_a, embedding_a, content="Bot A content", source_url="https://a.com")
    await _insert_chunk(db_session, bot_b, doc_b, embedding_b, content="Bot B content", source_url="https://b.com")
    await db_session.flush()

    # Query as bot A — the query vector matches bot A's chunk exactly
    results = await retrieve_chunks(bot_a, embedding_a, db_session, min_similarity=0.0)

    assert len(results) >= 1
    assert all(isinstance(r, RetrievedChunk) for r in results)
    assert all(r.source_url == "https://a.com" for r in results)


@pytest.mark.asyncio
async def test_cross_bot_isolation(db_session: AsyncSession):
    """Two bots with similar content: queries return only the correct bot's chunks."""
    user_id = await _insert_user(db_session)

    bot_x = await _insert_bot(db_session, user_id)
    job_x = await _insert_crawl_job(db_session, bot_x)
    doc_x = await _insert_document(db_session, bot_x, job_x)

    bot_y = await _insert_bot(db_session, user_id)
    job_y = await _insert_crawl_job(db_session, bot_y)
    doc_y = await _insert_document(db_session, bot_y, job_y)

    # Same embedding for both — simulates identical content
    shared_embedding = [0.5] * 1536

    await _insert_chunk(
        db_session, bot_x, doc_x, shared_embedding,
        content="Pricing info from X", source_url="https://x.com/pricing",
    )
    await _insert_chunk(
        db_session, bot_y, doc_y, shared_embedding,
        content="Pricing info from Y", source_url="https://y.com/pricing",
    )
    await db_session.flush()

    results_x = await retrieve_chunks(bot_x, shared_embedding, db_session, min_similarity=0.0)
    assert all(r.source_url == "https://x.com/pricing" for r in results_x)

    results_y = await retrieve_chunks(bot_y, shared_embedding, db_session, min_similarity=0.0)
    assert all(r.source_url == "https://y.com/pricing" for r in results_y)


@pytest.mark.asyncio
async def test_top_k_limiting(db_session: AsyncSession):
    """Results are limited to top_k (capped at MAX_TOP_K)."""
    user_id = await _insert_user(db_session)
    bot = await _insert_bot(db_session, user_id)
    job = await _insert_crawl_job(db_session, bot)
    doc = await _insert_document(db_session, bot, job)

    query_emb = [1.0] + [0.0] * 1535

    # Insert 8 chunks all with the same high-similarity embedding
    for i in range(8):
        await _insert_chunk(
            db_session, bot, doc, query_emb,
            content=f"Chunk number {i}",
            source_url=f"https://example.com/page-{i}",
            chunk_index=i,
        )
    await db_session.flush()

    results = await retrieve_chunks(bot, query_emb, db_session, top_k=3, min_similarity=0.0)
    assert len(results) <= 3


@pytest.mark.asyncio
async def test_empty_result_when_no_chunks_match(db_session: AsyncSession):
    """Returns empty list when no chunks exist for the bot."""
    user_id = await _insert_user(db_session)
    bot = await _insert_bot(db_session, user_id)
    await db_session.flush()

    query_emb = [1.0] + [0.0] * 1535
    results = await retrieve_chunks(bot, query_emb, db_session)

    assert results == []
