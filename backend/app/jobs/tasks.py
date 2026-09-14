"""
Celery Background Job Pipeline (PRD Section 9.1)
================================================
7 chained tasks implementing the full crawl→index pipeline:

  1. validate_url_task      — SSRF validation of the target URL
  2. discover_pages_task    — Sitemap + BFS page discovery
  3. crawl_pages_task       — Concurrent HTTP + Playwright crawling
  4. extract_and_brand_task — Content extraction + branding heuristics
  5. compile_knowledge_task — Build canonical website.md
  6. chunk_and_embed_task   — Chunk markdown + embed + store vectors
  7. finalize_crawl_task    — Compute final stats + set bot READY/FAILED

All tasks use synchronous SQLAlchemy sessions (SYNC_DATABASE_URL) because
Celery workers run in a synchronous event loop.  asyncio.run() is used to
bridge async service functions into the sync task context.
"""

import asyncio
import hashlib
import logging
import uuid
from datetime import datetime, timezone
from typing import List

from celery import chain
from sqlalchemy import create_engine, select, delete
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings
from app.jobs.celery_app import celery_app

logger = logging.getLogger("embediq.tasks")

# ---------------------------------------------------------------------------
# Synchronous DB session (Celery workers cannot use asyncpg)
# ---------------------------------------------------------------------------

_sync_engine = create_engine(
    settings.SYNC_DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=2,
)
SyncSession = sessionmaker(bind=_sync_engine, expire_on_commit=False)


def _get_sync_session() -> Session:
    return SyncSession()


# ---------------------------------------------------------------------------
# Stage update helpers
# ---------------------------------------------------------------------------

def _update_job_stage(db: Session, crawl_job_id: str, stage: str, **kwargs) -> None:
    """Update the crawl_job record's stage and any extra fields atomically."""
    from app.models.crawl_job import CrawlJob  # noqa: local import avoids circular

    job = db.get(CrawlJob, uuid.UUID(crawl_job_id))
    if not job:
        return
    job.stage = stage
    for key, value in kwargs.items():
        setattr(job, key, value)
    db.commit()


def _set_bot_status(db: Session, bot_id: str, status: str, last_error: str = None) -> None:
    """Update bot.status (and optionally last_error)."""
    from app.models.bot import Bot  # noqa

    bot = db.get(Bot, uuid.UUID(bot_id))
    if not bot:
        return
    bot.status = status
    if last_error is not None:
        bot.last_error = last_error
    db.commit()


def _fail_job(
    db: Session,
    bot_id: str,
    crawl_job_id: str,
    error_code: str,
    error_message: str,
) -> None:
    """Transition job + bot to FAILED state and record error details."""
    from app.models.crawl_job import CrawlJob

    job = db.get(CrawlJob, uuid.UUID(crawl_job_id))
    if job:
        job.status = "FAILED"
        job.error_code = error_code
        job.error_message = error_message
        job.completed_at = datetime.now(timezone.utc)
        db.commit()

    _set_bot_status(db, bot_id, "FAILED", last_error=error_message)


# ---------------------------------------------------------------------------
# Task 1 — URL Validation (SSRF guard)
# ---------------------------------------------------------------------------

@celery_app.task(bind=True, name="embediq.tasks.validate_url_task", max_retries=0)
def validate_url_task(self, bot_id: str, crawl_job_id: str) -> dict:
    """Validate target URL against SSRF policy (PRD 9.1 Task 1)."""
    from app.models.bot import Bot
    from app.services.ssrf_guard import validate_url

    logger.info("[validate_url] bot=%s job=%s", bot_id, crawl_job_id)
    db = _get_sync_session()
    try:
        _update_job_stage(
            db, crawl_job_id, "VALIDATING",
            status="RUNNING",
            started_at=datetime.now(timezone.utc),
        )
        _set_bot_status(db, bot_id, "CRAWLING")

        bot = db.get(Bot, uuid.UUID(bot_id))
        if not bot:
            raise ValueError(f"Bot {bot_id} not found")

        # SSRF check — raises ValueError on failure
        validate_url(bot.website_url)

        logger.info("[validate_url] PASS: %s", bot.website_url)
        return {"bot_id": bot_id, "crawl_job_id": crawl_job_id, "url": bot.website_url}

    except Exception as exc:
        logger.error("[validate_url] FAIL: %s", exc)
        _fail_job(db, bot_id, crawl_job_id, "SSRF_VALIDATION_FAILED", str(exc))
        raise
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Task 2 — Page Discovery
# ---------------------------------------------------------------------------

@celery_app.task(bind=True, name="embediq.tasks.discover_pages_task", max_retries=0)
def discover_pages_task(self, prev: dict) -> dict:
    """Discover all crawlable pages via sitemap + BFS (PRD 9.1 Task 2)."""
    from app.services.crawler import Crawler

    bot_id = prev["bot_id"]
    crawl_job_id = prev["crawl_job_id"]
    url = prev["url"]

    logger.info("[discover_pages] bot=%s url=%s", bot_id, url)
    db = _get_sync_session()
    try:
        _update_job_stage(db, crawl_job_id, "DISCOVERING")

        crawler = Crawler(origin=url, settings=settings)
        discovered_urls: List[str] = asyncio.run(crawler.discover_pages(url))

        _update_job_stage(db, crawl_job_id, "DISCOVERING", total_pages=len(discovered_urls))
        logger.info("[discover_pages] Found %d URLs", len(discovered_urls))

        return {
            "bot_id": bot_id,
            "crawl_job_id": crawl_job_id,
            "urls": discovered_urls,
        }

    except Exception as exc:
        logger.error("[discover_pages] FAIL: %s", exc)
        _fail_job(db, bot_id, crawl_job_id, "DISCOVERY_FAILED", str(exc))
        raise
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Task 3 — Page Crawling
# ---------------------------------------------------------------------------

@celery_app.task(bind=True, name="embediq.tasks.crawl_pages_task", max_retries=0)
def crawl_pages_task(self, prev: dict) -> dict:
    """Crawl all discovered pages (HTTP fast-path + Playwright fallback) (PRD 9.1 Task 3)."""
    from app.models.page import Page
    from app.services.crawler import Crawler

    bot_id = prev["bot_id"]
    crawl_job_id = prev["crawl_job_id"]
    urls: List[str] = prev["urls"]

    logger.info("[crawl_pages] bot=%s pages=%d", bot_id, len(urls))
    db = _get_sync_session()
    try:
        _update_job_stage(db, crawl_job_id, "CRAWLING")

        bot = db.get(
            __import__("app.models.bot", fromlist=["Bot"]).Bot,
            uuid.UUID(bot_id),
        )

        crawler = Crawler(origin=bot.website_url, settings=settings)
        results = asyncio.run(crawler.crawl_all(urls, concurrency=settings.CRAWL_CONCURRENCY_PER_BOT))

        # Fetch all existing pages in one query (Optimization)
        result_urls = [r.url for r in results]
        existing_pages_query = db.execute(
            select(Page).where(
                Page.bot_id == uuid.UUID(bot_id),
                Page.url.in_(result_urls)
            )
        ).scalars().all()

        # Map them for O(1) lookups
        existing_pages_map = {page.url: page for page in existing_pages_query}

        processed = 0
        failed = 0
        for result in results:
            # Upsert Page record
            existing = existing_pages_map.get(result.url)

            if existing:
                page = existing
            else:
                page = Page(
                    bot_id=uuid.UUID(bot_id),
                    crawl_job_id=uuid.UUID(crawl_job_id),
                    url=result.url,
                )
                db.add(page)

            page.title = result.title
            page.http_status = result.http_status
            page.content_type = result.content_type
            page.raw_html = result.raw_html[:500000] if result.raw_html else None  # cap at 500KB
            page.clean_text = result.clean_text
            page.content_hash = result.content_hash
            page.crawl_status = result.crawl_status
            page.render_mode = result.render_mode
            page.error_code = result.error_code
            page.error_message = result.error_message
            page.crawled_at = datetime.now(timezone.utc)

            if result.crawl_status == "SUCCESS":
                processed += 1
            else:
                failed += 1

        db.commit()
        _update_job_stage(
            db, crawl_job_id, "CRAWLING",
            processed_pages=processed,
            failed_pages=failed,
            warning_count=failed,
        )
        logger.info("[crawl_pages] processed=%d failed=%d", processed, failed)

        return {"bot_id": bot_id, "crawl_job_id": crawl_job_id}

    except Exception as exc:
        logger.error("[crawl_pages] FAIL: %s", exc)
        _fail_job(db, bot_id, crawl_job_id, "CRAWL_FAILED", str(exc))
        raise
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Task 4 — Content Extraction + Branding
# ---------------------------------------------------------------------------

@celery_app.task(bind=True, name="embediq.tasks.extract_and_brand_task", max_retries=0)
def extract_and_brand_task(self, prev: dict) -> dict:
    """Refine content extraction and extract visual branding (PRD 9.1 Task 4)."""
    from app.models.page import Page
    from app.models.brand import BrandSettings
    from app.services.extractor import extract_page_content, extract_branding
    from app.services.crawler import Crawler

    bot_id = prev["bot_id"]
    crawl_job_id = prev["crawl_job_id"]

    logger.info("[extract_and_brand] bot=%s", bot_id)
    db = _get_sync_session()
    try:
        _update_job_stage(db, crawl_job_id, "EXTRACTING")

        # Load all successfully crawled pages with raw HTML
        pages = db.execute(
            select(Page).where(
                Page.bot_id == uuid.UUID(bot_id),
                Page.crawl_job_id == uuid.UUID(crawl_job_id),
                Page.crawl_status == "SUCCESS",
                Page.raw_html.isnot(None),
            )
        ).scalars().all()

        root_page = None
        root_page_html = None

        for page in pages:
            if not page.raw_html:
                continue
            try:
                extracted = extract_page_content(page.raw_html, page.url)
                page.clean_text = extracted.clean_text
                page.structured_data = {
                    "headings": extracted.headings,
                    "paragraphs": extracted.structured_data.get("paragraphs", []),
                    "tables": extracted.structured_data.get("tables", []),
                    "title": extracted.title,
                    "description": extracted.description,
                }
                # Pick root page (shortest URL path) for branding
                if root_page is None or len(page.url) < len(root_page.url):
                    root_page = page
                    root_page_html = page.raw_html
            except Exception as e:
                logger.warning("[extract_and_brand] page %s extraction failed: %s", page.url, e)

        db.commit()

        # Branding extraction from root page
        _update_job_stage(db, crawl_job_id, "BRANDING")
        if root_page and root_page_html:
            try:
                branding = extract_branding(root_page_html, root_page.url)

                # Modern sites often keep brand colors/fonts in external CSS.
                # Always perform a dedicated rendered-branding pass on the root
                # page, even when the content crawl did not require Playwright.
                rendered_branding = {}
                try:
                    crawler = Crawler(origin=root_page.url, settings=settings)
                    rendered_branding = asyncio.run(
                        crawler.extract_rendered_branding(root_page.url)
                    )
                except Exception as rendered_exc:
                    logger.warning(
                        "[extract_and_brand] rendered branding failed: %s",
                        rendered_exc,
                    )

                brand = db.execute(
                    select(BrandSettings).where(BrandSettings.bot_id == uuid.UUID(bot_id))
                ).scalar_one_or_none()

                if brand:
                    conf = dict(branding.confidence or {})

                    if (
                        branding.company_name
                        and conf.get("company_name", 0) >= 0.5
                    ):
                        brand.company_name = branding.company_name

                    # Rendered values take precedence because they reflect
                    # external CSS and the browser's computed DOM.
                    rendered_logo = rendered_branding.get("logo_url")
                    if rendered_logo:
                        brand.logo_url = rendered_logo
                        conf["logo_url"] = 0.95
                    elif (
                        branding.logo_url
                        and conf.get("logo_url", 0) >= 0.5
                    ):
                        brand.logo_url = branding.logo_url

                    if branding.favicon_url:
                        brand.favicon_url = branding.favicon_url

                    rendered_primary = rendered_branding.get("primary_color")
                    if rendered_primary:
                        brand.primary_color = rendered_primary
                        conf["primary_color"] = 0.90
                    elif (
                        branding.primary_color
                        and conf.get("primary_color", 0) >= 0.5
                    ):
                        brand.primary_color = branding.primary_color

                    rendered_secondary = rendered_branding.get("secondary_color")
                    if rendered_secondary:
                        brand.secondary_color = rendered_secondary
                        conf["secondary_color"] = 0.85
                    elif (
                        branding.secondary_color
                        and conf.get("secondary_color", 0) >= 0.5
                    ):
                        brand.secondary_color = branding.secondary_color

                    rendered_accent = rendered_branding.get("accent_color")
                    if rendered_accent:
                        brand.accent_color = rendered_accent
                        conf["accent_color"] = 0.85
                    elif (
                        branding.accent_color
                        and conf.get("accent_color", 0) >= 0.5
                    ):
                        brand.accent_color = branding.accent_color

                    rendered_background = rendered_branding.get("background_color")
                    if rendered_background:
                        brand.background_color = rendered_background
                        conf["background_color"] = 0.90
                    elif (
                        branding.background_color
                        and conf.get("background_color", 0) >= 0.5
                    ):
                        brand.background_color = branding.background_color

                    rendered_text = rendered_branding.get("text_color")
                    if rendered_text:
                        brand.text_color = rendered_text
                        conf["text_color"] = 0.90
                    elif (
                        branding.text_color
                        and conf.get("text_color", 0) >= 0.5
                    ):
                        brand.text_color = branding.text_color

                    rendered_font = rendered_branding.get("font_family")
                    if rendered_font:
                        brand.font_family = rendered_font[:200]
                        conf["font_family"] = 0.90
                    elif (
                        branding.font_family
                        and conf.get("font_family", 0) >= 0.5
                    ):
                        brand.font_family = branding.font_family

                    # Corroborate CSS-derived colors with the actual logo. Modern
                    # sites frequently expose generic framework colors (Bootstrap,
                    # toast libraries, warning states) that otherwise outrank the
                    # real brand accent. A strong chromatic logo color is a better
                    # primary-brand signal than those generic UI colors.
                    if brand.logo_url:
                        try:
                            from app.services.logo_palette import extract_logo_palette
                            logo_palette = extract_logo_palette(brand.logo_url)
                            if logo_palette:
                                brand.primary_color = logo_palette[0]
                                conf["primary_color"] = 0.96
                                conf["primary_color_source"] = "logo_palette"
                            if len(logo_palette) > 1:
                                brand.accent_color = logo_palette[1]
                                conf["accent_color"] = 0.92
                                conf["accent_color_source"] = "logo_palette"
                            conf["logo_palette"] = logo_palette
                        except Exception as palette_exc:
                            logger.warning("[extract_and_brand] logo palette failed: %s", palette_exc)

                    conf["rendered_branding"] = bool(rendered_branding)
                    brand.confidence = conf
                    db.commit()

                    logger.info(
                        "[extract_and_brand] branding saved: logo=%s primary=%s "
                        "secondary=%s background=%s text=%s font=%s rendered=%s",
                        bool(brand.logo_url),
                        brand.primary_color,
                        brand.secondary_color,
                        brand.background_color,
                        brand.text_color,
                        brand.font_family,
                        bool(rendered_branding),
                    )
            except Exception as e:
                logger.warning("[extract_and_brand] branding failed: %s", e)

        return {"bot_id": bot_id, "crawl_job_id": crawl_job_id}

    except Exception as exc:
        logger.error("[extract_and_brand] FAIL: %s", exc)
        _fail_job(db, bot_id, crawl_job_id, "EXTRACTION_FAILED", str(exc))
        raise
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Task 5 — Compile Knowledge Base (website.md)
# ---------------------------------------------------------------------------

@celery_app.task(bind=True, name="embediq.tasks.compile_knowledge_task", max_retries=0)
def compile_knowledge_task(self, prev: dict) -> dict:
    """Build the canonical website.md document (PRD 9.1 Task 5)."""
    from app.models.page import Page
    from app.models.document import Document
    from app.models.brand import BrandSettings
    from app.services.knowledge_builder import build_website_md, PageData

    bot_id = prev["bot_id"]
    crawl_job_id = prev["crawl_job_id"]

    logger.info("[compile_knowledge] bot=%s", bot_id)
    db = _get_sync_session()
    try:
        _update_job_stage(db, crawl_job_id, "GENERATING_KNOWLEDGE")

        # Load successful pages
        pages = db.execute(
            select(Page).where(
                Page.bot_id == uuid.UUID(bot_id),
                Page.crawl_status == "SUCCESS",
            )
        ).scalars().all()

        brand = db.execute(
            select(BrandSettings).where(BrandSettings.bot_id == uuid.UUID(bot_id))
        ).scalar_one_or_none()

        bot = db.get(
            __import__("app.models.bot", fromlist=["Bot"]).Bot,
            uuid.UUID(bot_id),
        )

        company_name = (brand.company_name if brand and brand.company_name else None) or bot.name

        page_data_list = [
            PageData(
                url=p.url,
                title=p.title or "Untitled",
                clean_text=p.clean_text or "",
                structured_data=p.structured_data or {},
            )
            for p in pages
        ]

        job = db.get(
            __import__("app.models.crawl_job", fromlist=["CrawlJob"]).CrawlJob,
            uuid.UUID(crawl_job_id),
        )

        markdown_content = build_website_md(
            bot_id=bot_id,
            crawl_job_id=crawl_job_id,
            website_url=bot.website_url,
            website_name=company_name,
            pages=page_data_list,
            failed_pages=job.failed_pages if job else 0,
        )

        content_hash = hashlib.sha256(markdown_content.encode()).hexdigest()

        # Delete old documents for this bot
        db.execute(
            delete(Document).where(Document.bot_id == uuid.UUID(bot_id))
        )

        doc = Document(
            bot_id=uuid.UUID(bot_id),
            crawl_job_id=uuid.UUID(crawl_job_id),
            type="CANONICAL_MARKDOWN",
            content=markdown_content,
            content_hash=content_hash,
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        logger.info("[compile_knowledge] document_id=%s chars=%d", doc.id, len(markdown_content))
        return {"bot_id": bot_id, "crawl_job_id": crawl_job_id, "document_id": str(doc.id)}

    except Exception as exc:
        logger.error("[compile_knowledge] FAIL: %s", exc)
        _fail_job(db, bot_id, crawl_job_id, "KNOWLEDGE_FAILED", str(exc))
        raise
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Task 6 — Chunk + Embed + Index
# ---------------------------------------------------------------------------

@celery_app.task(bind=True, name="embediq.tasks.chunk_and_embed_task", max_retries=0)
def chunk_and_embed_task(self, prev: dict) -> dict:
    """Chunk markdown, embed, and write vectors to pgvector (PRD 9.1 Task 6)."""
    from app.models.document import Document
    from app.models.chunk import Chunk
    from app.services.chunker import MarkdownChunker
    from app.services.embedding_service import embed_chunks_batch

    bot_id = prev["bot_id"]
    crawl_job_id = prev["crawl_job_id"]
    document_id = prev["document_id"]

    logger.info("[chunk_and_embed] bot=%s doc=%s", bot_id, document_id)
    db = _get_sync_session()
    try:
        _update_job_stage(db, crawl_job_id, "CHUNKING")

        doc = db.get(Document, uuid.UUID(document_id))
        if not doc:
            raise ValueError(f"Document {document_id} not found")

        chunker = MarkdownChunker(
            target_tokens=settings.TARGET_CHUNK_TOKENS,
            max_tokens=settings.MAX_CHUNK_TOKENS,
            overlap_tokens=settings.CHUNK_OVERLAP_TOKENS,
        )
        chunks = chunker.chunk_document(doc.content)
        logger.info("[chunk_and_embed] %d chunks produced", len(chunks))

        # Embed
        _update_job_stage(db, crawl_job_id, "EMBEDDING")
        texts = [c.content for c in chunks]
        embeddings: List[List[float]] = asyncio.run(embed_chunks_batch(texts))

        # Delete existing chunks for this bot (supports re-crawl)
        _update_job_stage(db, crawl_job_id, "INDEXING")
        db.execute(delete(Chunk).where(Chunk.bot_id == uuid.UUID(bot_id)))
        db.commit()

        # Insert new chunk records
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            db_chunk = Chunk(
                bot_id=uuid.UUID(bot_id),
                document_id=uuid.UUID(document_id),
                source_url=chunk.source_url,
                page_title=chunk.page_title,
                heading_path=chunk.heading_path,
                content=chunk.content,
                content_hash=chunk.content_hash,
                chunk_index=chunk.chunk_index,
                token_count=chunk.token_count,
                embedding=embedding,
                metadata_={},
            )
            db.add(db_chunk)

        db.commit()
        logger.info("[chunk_and_embed] Indexed %d chunks for bot=%s", len(chunks), bot_id)

        return {"bot_id": bot_id, "crawl_job_id": crawl_job_id, "chunk_count": len(chunks)}

    except Exception as exc:
        logger.error("[chunk_and_embed] FAIL: %s", exc)
        _fail_job(db, bot_id, crawl_job_id, "EMBEDDING_FAILED", str(exc))
        raise
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Task 7 — Finalize Crawl
# ---------------------------------------------------------------------------

@celery_app.task(bind=True, name="embediq.tasks.finalize_crawl_task", max_retries=0)
def finalize_crawl_task(self, prev: dict) -> dict:
    """Transition bot to READY/READY_WITH_WARNINGS/FAILED (PRD 9.1 Task 7)."""
    from app.models.crawl_job import CrawlJob

    bot_id = prev["bot_id"]
    crawl_job_id = prev["crawl_job_id"]
    chunk_count = prev.get("chunk_count", 0)

    logger.info("[finalize_crawl] bot=%s chunks=%d", bot_id, chunk_count)
    db = _get_sync_session()
    try:
        job = db.get(CrawlJob, uuid.UUID(crawl_job_id))
        failed_pages = job.failed_pages if job else 0

        if chunk_count > 0 and failed_pages == 0:
            final_status = "READY"
        elif chunk_count > 0 and failed_pages > 0:
            final_status = "READY_WITH_WARNINGS"
        else:
            final_status = "FAILED"

        _set_bot_status(db, bot_id, final_status)
        _update_job_stage(
            db, crawl_job_id, "COMPLETED",
            status="COMPLETED",
            completed_at=datetime.now(timezone.utc),
        )

        logger.info("[finalize_crawl] bot=%s status=%s", bot_id, final_status)
        return {"bot_id": bot_id, "status": final_status}

    except Exception as exc:
        logger.error("[finalize_crawl] FAIL: %s", exc)
        _fail_job(db, bot_id, crawl_job_id, "FINALIZE_FAILED", str(exc))
        raise
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Pipeline entry point — chain all 7 tasks
# ---------------------------------------------------------------------------

def enqueue_crawl_pipeline(bot_id: str, crawl_job_id: str) -> None:
    """Enqueue the full 7-task crawl pipeline as a Celery chain.

    Args:
        bot_id: UUID string of the bot to process.
        crawl_job_id: UUID string of the crawl job to update with progress.
    """
    pipeline = chain(
        validate_url_task.si(bot_id, crawl_job_id),
        discover_pages_task.s(),
        crawl_pages_task.s(),
        extract_and_brand_task.s(),
        compile_knowledge_task.s(),
        chunk_and_embed_task.s(),
        finalize_crawl_task.s(),
    )
    pipeline.apply_async()
    logger.info("Enqueued crawl pipeline for bot=%s job=%s", bot_id, crawl_job_id)
