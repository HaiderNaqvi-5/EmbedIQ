"""
Bot Management API (PRD Section 8.2)
=====================================
All endpoints require a valid JWT bearer token.
Ownership is enforced via the `get_bot_for_user` dependency which returns 404
if the bot doesn't exist OR belongs to a different user.
"""

import re
from typing import List
from urllib.parse import urlparse

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.deps import get_current_user, get_bot_for_user
from app.models.user import User
from app.models.bot import Bot
from app.models.crawl_job import CrawlJob
from app.models.document import Document
from app.models.chunk import Chunk
from app.models.brand import BrandSettings
from app.models.page import Page
from app.schemas.bot import (
    BotCreateRequest,
    BotCreateResponse,
    BotResponse,
    BotDetailResponse,
    CrawlStatusResponse,
    KnowledgeResponse,
)
from app.schemas.brand import BrandSettingsResponse, BrandSettingsUpdateRequest

router = APIRouter(prefix="/bots", tags=["Bots"])


def _normalize_origin(url: str) -> str:
    """Extract and return the scheme+host (origin) from a URL string.

    Example: "https://www.example.com/path?q=1" → "https://www.example.com"
    """
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def _extract_domain(url: str) -> str:
    """Return just the hostname portion of a URL for use as a default bot name.

    Example: "https://www.example.com/path" → "example.com"
    """
    parsed = urlparse(url)
    host = parsed.netloc
    # Strip leading 'www.'
    host = re.sub(r"^www\.", "", host)
    return host


# ---------------------------------------------------------------------------
# POST /api/bots  — Create a new bot
# ---------------------------------------------------------------------------
@router.post("", response_model=BotCreateResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_bot(
    req: BotCreateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new chatbot, persist initial records, and queue the crawl job.

    - Validates that `website_url` is a valid http/https URL.
    - Normalises the URL to its origin (scheme + host).
    - Defaults `name` to the bare domain if not supplied.
    - Creates: Bot (PENDING), CrawlJob (QUEUED/QUEUED), and default BrandSettings.
    - Celery crawl pipeline dispatched as a background task after DB commit.
    - Returns HTTP 202 with bot_id, job_id, name, website_url, status, created_at.
    """
    # ── Validate URL scheme ──────────────────────────────────────────────────
    url = req.website_url.strip()
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "INVALID_URL",
                "message": "website_url must be a valid http or https URL",
            },
        )

    # ── Derive canonical values ──────────────────────────────────────────────
    normalized_origin = _normalize_origin(url)
    name = req.name.strip() if req.name else _extract_domain(url)

    # ── Persist Bot record ───────────────────────────────────────────────────
    bot = Bot(
        user_id=current_user.id,
        name=name,
        website_url=url,
        normalized_origin=normalized_origin,
        status="PENDING",
    )
    db.add(bot)
    await db.flush()  # populate bot.id without committing the transaction

    # ── Persist CrawlJob record ──────────────────────────────────────────────
    crawl_job = CrawlJob(
        bot_id=bot.id,
        status="QUEUED",
        stage="QUEUED",
    )
    db.add(crawl_job)

    # ── Persist default BrandSettings ────────────────────────────────────────
    brand = BrandSettings(bot_id=bot.id)
    db.add(brand)

    await db.commit()
    await db.refresh(bot)
    await db.refresh(crawl_job)

    # Dispatch Celery ingestion pipeline AFTER transaction is committed
    bot_id_str = str(bot.id)
    job_id_str = str(crawl_job.id)

    def _dispatch():
        try:
            from app.jobs.tasks import enqueue_crawl_pipeline
            enqueue_crawl_pipeline(bot_id_str, job_id_str)
        except Exception as e:
            import logging as _logging
            _logging.getLogger("embediq.bots").warning(
                "Could not enqueue crawl pipeline (worker may be offline): %s", e
            )

    background_tasks.add_task(_dispatch)

    return BotCreateResponse(
        bot_id=bot.id,
        job_id=crawl_job.id,
        name=bot.name,
        website_url=bot.website_url,
        status=bot.status,
        created_at=bot.created_at,
    )


# ---------------------------------------------------------------------------
# GET /api/bots  — List all bots for the authenticated user
# ---------------------------------------------------------------------------
@router.get("", response_model=List[BotResponse])
async def list_bots(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return all chatbots owned by the authenticated user, ordered newest-first."""
    result = await db.execute(
        select(Bot)
        .where(Bot.user_id == current_user.id)
        .order_by(Bot.created_at.desc())
    )
    bots = result.scalars().all()
    return bots


# ---------------------------------------------------------------------------
# GET /api/bots/{bot_id}  — Get bot detail with page + chunk counts
# ---------------------------------------------------------------------------
@router.get("/{bot_id}", response_model=BotDetailResponse)
async def get_bot(
    bot: Bot = Depends(get_bot_for_user),
    db: AsyncSession = Depends(get_db),
):
    """Return detailed information about a specific bot.

    Includes total pages indexed and total chunks produced for that bot.
    Ownership is enforced via `get_bot_for_user`; returns 404 if not found or
    not owned by the requesting user.
    """
    # Count indexed pages (pages that were crawled successfully)
    page_count_result = await db.execute(
        select(func.count(Page.id)).where(
            Page.bot_id == bot.id,
            Page.crawl_status == "SUCCESS",
        )
    )
    total_pages = page_count_result.scalar_one() or 0

    # Count chunks
    chunk_count_result = await db.execute(
        select(func.count(Chunk.id)).where(Chunk.bot_id == bot.id)
    )
    total_chunks = chunk_count_result.scalar_one() or 0

    # Eagerly load brand settings
    brand_result = await db.execute(
        select(BrandSettings).where(BrandSettings.bot_id == bot.id)
    )
    brand = brand_result.scalar_one_or_none()

    return BotDetailResponse(
        id=bot.id,
        user_id=bot.user_id,
        name=bot.name,
        website_url=bot.website_url,
        normalized_origin=bot.normalized_origin,
        status=bot.status,
        last_error=bot.last_error,
        created_at=bot.created_at,
        updated_at=bot.updated_at,
        branding=BrandSettingsResponse.model_validate(brand) if brand else None,
        total_pages_indexed=total_pages,
        total_chunks=total_chunks,
    )


# ---------------------------------------------------------------------------
# GET /api/bots/{bot_id}/crawl/status  — Latest crawl job status
# ---------------------------------------------------------------------------
@router.get("/{bot_id}/crawl/status", response_model=CrawlStatusResponse)
async def get_crawl_status(
    bot: Bot = Depends(get_bot_for_user),
    db: AsyncSession = Depends(get_db),
):
    """Return the status of the most recent crawl job for the specified bot.

    If no crawl job exists yet (e.g. bot was just created and the worker hasn't
    started), a synthetic QUEUED status is returned using the bot's own id so
    the caller always receives a valid response shape.
    """
    result = await db.execute(
        select(CrawlJob)
        .where(CrawlJob.bot_id == bot.id)
        .order_by(CrawlJob.created_at.desc())
        .limit(1)
    )
    job = result.scalar_one_or_none()

    if not job:
        # No job record found — surface a synthetic pending status
        return CrawlStatusResponse(
            bot_id=bot.id,
            job_id=None,
            status="QUEUED",
            stage="QUEUED",
            total_pages=0,
            processed_pages=0,
            failed_pages=0,
            warning_count=0,
        )

    return CrawlStatusResponse(
        bot_id=bot.id,
        job_id=job.id,
        status=job.status,
        stage=job.stage,
        total_pages=job.total_pages,
        processed_pages=job.processed_pages,
        failed_pages=job.failed_pages,
        warning_count=job.warning_count,
        error_code=job.error_code,
        error_message=job.error_message,
        started_at=job.started_at,
        completed_at=job.completed_at,
    )


# ---------------------------------------------------------------------------
# GET /api/bots/{bot_id}/knowledge  — Canonical website.md and chunk count
# ---------------------------------------------------------------------------
@router.get("/{bot_id}/knowledge", response_model=KnowledgeResponse)
async def get_knowledge(
    bot: Bot = Depends(get_bot_for_user),
    db: AsyncSession = Depends(get_db),
):
    """Return the canonical CANONICAL_MARKDOWN document and chunk count for the bot.

    If the bot hasn't finished crawling yet, document_id and markdown_content
    will be None and chunk_count will be 0.
    """
    # Fetch the canonical document (most recent if multiple exist)
    doc_result = await db.execute(
        select(Document)
        .where(
            Document.bot_id == bot.id,
            Document.type == "CANONICAL_MARKDOWN",
        )
        .order_by(Document.created_at.desc())
        .limit(1)
    )
    doc = doc_result.scalar_one_or_none()

    # Count chunks for this bot
    chunk_count_result = await db.execute(
        select(func.count(Chunk.id)).where(Chunk.bot_id == bot.id)
    )
    chunk_count = chunk_count_result.scalar_one() or 0

    return KnowledgeResponse(
        bot_id=bot.id,
        document_id=doc.id if doc else None,
        markdown_content=doc.content if doc else None,
        chunk_count=chunk_count,
        last_indexed_at=doc.created_at if doc else None,
    )


# ---------------------------------------------------------------------------
# GET /api/bots/{bot_id}/branding  — Get branding settings
# ---------------------------------------------------------------------------
@router.get("/{bot_id}/branding", response_model=BrandSettingsResponse)
async def get_branding(
    bot: Bot = Depends(get_bot_for_user),
    db: AsyncSession = Depends(get_db),
):
    """Return the current branding / visual theme configuration for this bot."""
    result = await db.execute(
        select(BrandSettings).where(BrandSettings.bot_id == bot.id)
    )
    brand = result.scalar_one_or_none()

    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "BRAND_NOT_FOUND",
                "message": "Branding settings not found for this bot",
            },
        )

    return brand


# ---------------------------------------------------------------------------
# PATCH /api/bots/{bot_id}/branding  — Update branding settings
# ---------------------------------------------------------------------------
@router.patch("/{bot_id}/branding", response_model=BrandSettingsResponse)
async def update_branding(
    req: BrandSettingsUpdateRequest,
    bot: Bot = Depends(get_bot_for_user),
    db: AsyncSession = Depends(get_db),
):
    """Partially update the branding settings for this bot.

    Only fields present in the request body (non-None) are updated; all other
    fields retain their current values.
    """
    result = await db.execute(
        select(BrandSettings).where(BrandSettings.bot_id == bot.id)
    )
    brand = result.scalar_one_or_none()

    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "BRAND_NOT_FOUND",
                "message": "Branding settings not found for this bot",
            },
        )

    # Apply only the supplied (non-None) fields
    update_data = req.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(brand, field, value)

    await db.commit()
    await db.refresh(brand)
    return brand


# ---------------------------------------------------------------------------
# DELETE /api/bots/{bot_id}  — Delete bot and all associated data
# ---------------------------------------------------------------------------
@router.delete("/{bot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bot(
    bot: Bot = Depends(get_bot_for_user),
    db: AsyncSession = Depends(get_db),
):
    """Permanently delete a bot and all associated data (cascade).

    All related records — crawl jobs, pages, documents, chunks, brand settings,
    and conversations — are removed by the database's ON DELETE CASCADE rules.
    Returns HTTP 204 No Content on success.
    """
    await db.delete(bot)
    await db.commit()
