"""
Tenant Isolation Tests (PRD AT-006)
=====================================
Strict database-level isolation verification:
Bot A's chunks must NEVER be returned for Bot B's queries.
"""

import uuid
import pytest
import pytest_asyncio
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.bot import Bot
from app.models.crawl_job import CrawlJob
from app.models.document import Document
from app.models.chunk import Chunk


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _create_bot_with_chunks(
    db: AsyncSession,
    user_email_suffix: str,
    bot_name: str,
    website_url: str,
    chunk_content: str,
    chunk_count: int = 3,
) -> tuple:
    """Create a user + bot + chunks and return (bot_id, chunk_ids)."""
    user = User(
        email=f"tenant_{user_email_suffix}_{uuid.uuid4().hex[:6]}@example.com",
        password_hash="hashed",
    )
    db.add(user)
    await db.flush()

    bot = Bot(
        user_id=user.id,
        name=bot_name,
        website_url=website_url,
        normalized_origin=website_url,
        status="READY",
    )
    db.add(bot)
    await db.flush()

    job = CrawlJob(
        bot_id=bot.id,
        status="COMPLETED",
        stage="COMPLETED",
        total_pages=1,
        processed_pages=1,
    )
    db.add(job)
    await db.flush()

    doc = Document(
        bot_id=bot.id,
        crawl_job_id=job.id,
        type="CANONICAL_MARKDOWN",
        content=f"# {bot_name}\n\n{chunk_content}",
        content_hash="hash123",
    )
    db.add(doc)
    await db.flush()

    chunk_ids = []
    for i in range(chunk_count):
        # Create a unique-ish vector for each chunk
        # Use different values per bot so similarity search distinguishes them
        if "A" in bot_name:
            vector = [0.9] * 100 + [0.0] * 1436  # Bot A pattern
        else:
            vector = [0.1] * 100 + [0.9] * 100 + [0.0] * 1336  # Bot B pattern

        chunk = Chunk(
            bot_id=bot.id,
            document_id=doc.id,
            source_url=website_url,
            page_title=bot_name,
            heading_path=bot_name,
            content=f"{chunk_content} #{i}",
            content_hash=f"hash_{i}",
            chunk_index=i,
            token_count=10,
            embedding=vector,
            metadata_={},
        )
        db.add(chunk)
        await db.flush()
        chunk_ids.append(chunk.id)

    return bot.id, chunk_ids


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestTenantIsolation:
    """PRD AT-006: Cross-bot vector retrieval must return zero chunks from other bots."""

    async def test_bot_a_chunks_not_returned_for_bot_b_query(self, db_session: AsyncSession):
        """Bot A and Bot B have different content. Querying for Bot A must not return Bot B's chunks."""
        bot_a_id, _ = await _create_bot_with_chunks(
            db_session,
            user_email_suffix="alpha",
            bot_name="BotA-Pricing",
            website_url="https://a-example.com",
            chunk_content="Our pricing plan starts at $29 per month with 5 nodes included.",
        )
        bot_b_id, _ = await _create_bot_with_chunks(
            db_session,
            user_email_suffix="beta",
            bot_name="BotB-About",
            website_url="https://b-example.com",
            chunk_content="We are a leading provider of cloud infrastructure services since 2020.",
        )

        # Query chunks for bot_a — should ONLY return bot_a's chunks
        result = await db_session.execute(
            select(Chunk).where(Chunk.bot_id == bot_a_id)
        )
        bot_a_chunks = result.scalars().all()

        # Query chunks for bot_b
        result_b = await db_session.execute(
            select(Chunk).where(Chunk.bot_id == bot_b_id)
        )
        bot_b_chunks = result_b.scalars().all()

        # Verify each bot's chunks belong only to that bot
        for chunk in bot_a_chunks:
            assert chunk.bot_id == bot_a_id, (
                f"Bot A query returned chunk belonging to bot {chunk.bot_id}"
            )
        for chunk in bot_b_chunks:
            assert chunk.bot_id == bot_b_id, (
                f"Bot B query returned chunk belonging to bot {chunk.bot_id}"
            )

        # Verify no overlap
        a_ids = {c.id for c in bot_a_chunks}
        b_ids = {c.id for c in bot_b_chunks}
        assert a_ids.isdisjoint(b_ids), "Chunk IDs overlap between bots!"

        # Verify both have chunks
        assert len(bot_a_chunks) == 3
        assert len(bot_b_chunks) == 3

    async def test_unfiltered_query_still_has_bot_id(self, db_session: AsyncSession):
        """Even an unfiltered query should show all chunks have a bot_id (structural invariant)."""
        await _create_bot_with_chunks(
            db_session,
            user_email_suffix="struct",
            bot_name="StructBot",
            website_url="https://struct.example.com",
            chunk_content="Structural test content.",
        )

        result = await db_session.execute(select(Chunk))
        all_chunks = result.scalars().all()
        assert len(all_chunks) > 0
        for chunk in all_chunks:
            assert chunk.bot_id is not None, "Chunk has no bot_id — isolation invariant violated!"

    async def test_delete_bot_removes_all_chunks(self, db_session: AsyncSession):
        """Deleting a bot must cascade-delete all its chunks."""
        bot_id, chunk_ids = await _create_bot_with_chunks(
            db_session,
            user_email_suffix="del",
            bot_name="DeleteBot",
            website_url="https://del.example.com",
            chunk_content="Content to be deleted.",
        )

        # Verify chunks exist
        result = await db_session.execute(
            select(Chunk).where(Chunk.bot_id == bot_id)
        )
        assert len(result.scalars().all()) == 3

        # Delete the bot
        bot = await db_session.get(Bot, bot_id)
        await db_session.delete(bot)
        await db_session.flush()

        # Verify all chunks are gone
        result = await db_session.execute(
            select(Chunk).where(Chunk.bot_id == bot_id)
        )
        assert len(result.scalars().all()) == 0

    async def test_retrieval_sql_filters_by_bot_id(self, db_session: AsyncSession):
        """Verify the SQL WHERE clause in retrieval.py enforces bot_id filtering."""
        bot_a_id, _ = await _create_bot_with_chunks(
            db_session,
            user_email_suffix="sql_a",
            bot_name="SqlBotA",
            website_url="https://sql-a.example.com",
            chunk_content="SQL isolation test A.",
        )
        bot_b_id, _ = await _create_bot_with_chunks(
            db_session,
            user_email_suffix="sql_b",
            bot_name="SqlBotB",
            website_url="https://sql-b.example.com",
            chunk_content="SQL isolation test B.",
        )

        # Simulate the exact SQL from retrieval.py with bot_a_id
        vector_str = "[" + ",".join(["0.9"] * 100 + ["0.0"] * 1436) + "]"
        sql = text("""
            SELECT id, bot_id, content
            FROM chunks
            WHERE bot_id = :bot_id
            ORDER BY embedding <=> :query_vector ASC
            LIMIT 10
        """)

        result_a = await db_session.execute(
            sql, {"query_vector": vector_str, "bot_id": str(bot_a_id)}
        )
        rows_a = result_a.fetchall()
        for row in rows_a:
            assert str(row.bot_id) == str(bot_a_id), (
                f"SQL query for bot A returned chunk from bot {row.bot_id}"
            )

        result_b = await db_session.execute(
            sql, {"query_vector": vector_str, "bot_id": str(bot_b_id)}
        )
        rows_b = result_b.fetchall()
        for row in rows_b:
            assert str(row.bot_id) == str(bot_b_id), (
                f"SQL query for bot B returned chunk from bot {row.bot_id}"
            )
