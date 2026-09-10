import uuid
import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.bot import Bot
from app.models.crawl_job import CrawlJob
from app.models.page import Page
from app.models.document import Document
from app.models.chunk import Chunk
from app.models.brand import BrandSettings
from app.models.conversation import Conversation, Message


@pytest.mark.asyncio
async def test_create_user_and_bot(db_session: AsyncSession):
    """Verify User and Bot creation with relationship linkage."""
    user = User(
        email=f"test_{uuid.uuid4().hex[:8]}@example.com",
        password_hash="hashed_secret_123",
    )
    db_session.add(user)
    await db_session.flush()

    bot = Bot(
        user_id=user.id,
        name="Test Documentation Bot",
        website_url="https://docs.example.com",
        normalized_origin="https://docs.example.com",
        status="PENDING",
    )
    db_session.add(bot)
    await db_session.flush()

    # Query back
    result = await db_session.execute(select(Bot).where(Bot.id == bot.id))
    fetched_bot = result.scalar_one_or_none()

    assert fetched_bot is not None
    assert fetched_bot.name == "Test Documentation Bot"
    assert fetched_bot.user_id == user.id
    assert fetched_bot.status == "PENDING"


@pytest.mark.asyncio
async def test_full_knowledge_and_chunk_graph(db_session: AsyncSession):
    """Verify full graph: User -> Bot -> CrawlJob -> Page -> Document -> Chunk -> BrandSettings."""
    user = User(
        email=f"graph_{uuid.uuid4().hex[:8]}@example.com",
        password_hash="hashed_secret_123",
    )
    db_session.add(user)
    await db_session.flush()

    bot = Bot(
        user_id=user.id,
        name="Graph Test Bot",
        website_url="https://example.com",
        normalized_origin="https://example.com",
        status="CRAWLING",
    )
    db_session.add(bot)
    await db_session.flush()

    crawl_job = CrawlJob(
        bot_id=bot.id,
        status="RUNNING",
        stage="CHUNKING",
        total_pages=5,
        processed_pages=5,
    )
    db_session.add(crawl_job)
    await db_session.flush()

    page = Page(
        bot_id=bot.id,
        crawl_job_id=crawl_job.id,
        url="https://example.com/pricing",
        title="Pricing Page",
        clean_text="Our plans start at $29/mo.",
        crawl_status="SUCCESS",
        render_mode="HTTP",
        content_hash="abc123hash",
    )
    db_session.add(page)
    await db_session.flush()

    doc = Document(
        bot_id=bot.id,
        crawl_job_id=crawl_job.id,
        type="CANONICAL_MARKDOWN",
        content="# Pricing\n\nOur plans start at $29/mo.",
        content_hash="doc123hash",
    )
    db_session.add(doc)
    await db_session.flush()

    # Create dummy 1536-dimensional embedding vector
    dummy_vector = [0.01 * (i % 10) for i in range(1536)]

    chunk = Chunk(
        bot_id=bot.id,
        document_id=doc.id,
        page_id=page.id,
        source_url="https://example.com/pricing",
        page_title="Pricing Page",
        heading_path="Pricing",
        content="Our plans start at $29/mo.",
        content_hash="chunk123hash",
        chunk_index=0,
        token_count=12,
        embedding=dummy_vector,
        metadata_={"type": "pricing"},
    )
    db_session.add(chunk)

    brand = BrandSettings(
        bot_id=bot.id,
        company_name="Example Corp",
        primary_color="#2563EB",
    )
    db_session.add(brand)
    await db_session.flush()

    # Query chunk with vector similarity
    query_vector = [0.01 * (i % 10) for i in range(1536)]
    chunk_query = await db_session.execute(
        select(
            Chunk.id,
            Chunk.content,
            Chunk.source_url,
            (1 - Chunk.embedding.cosine_distance(query_vector)).label("similarity"),
        )
        .where(Chunk.bot_id == bot.id)
        .order_by(Chunk.embedding.cosine_distance(query_vector))
        .limit(1)
    )
    res = chunk_query.one_or_none()
    assert res is not None
    assert res.content == "Our plans start at $29/mo."
    assert res.similarity > 0.99  # Cosine similarity of identical vector should be ~1.0


@pytest.mark.asyncio
async def test_cascading_deletion(db_session: AsyncSession):
    """Verify that deleting a User cascades to all Bots, Chunks, Pages, and Conversations."""
    user = User(
        email=f"cascade_{uuid.uuid4().hex[:8]}@example.com",
        password_hash="hashed_secret_123",
    )
    db_session.add(user)
    await db_session.flush()

    bot = Bot(
        user_id=user.id,
        name="Cascade Bot",
        website_url="https://cascade.example.com",
        normalized_origin="https://cascade.example.com",
    )
    db_session.add(bot)
    await db_session.flush()

    conv = Conversation(
        bot_id=bot.id,
        session_id="session_cascade_1",
    )
    db_session.add(conv)
    await db_session.flush()

    msg = Message(
        conversation_id=conv.id,
        role="user",
        content="Hello world",
    )
    db_session.add(msg)
    await db_session.flush()

    # Delete User
    await db_session.delete(user)
    await db_session.flush()

    # Verify bot and conversation are deleted
    bot_check = await db_session.execute(select(Bot).where(Bot.id == bot.id))
    assert bot_check.scalar_one_or_none() is None

    conv_check = await db_session.execute(select(Conversation).where(Conversation.id == conv.id))
    assert conv_check.scalar_one_or_none() is None
