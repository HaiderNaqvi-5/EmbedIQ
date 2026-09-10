# Session: Celery Background Job Pipeline (Milestone 6)

## Status: COMPLETE

## Date
2026-09-09

## Summary
Implemented the 7-task Celery pipeline that orchestrates the full website ingestion workflow from URL validation to vector indexing.

## Files Created

- `backend/app/jobs/__init__.py` — Package init
- `backend/app/jobs/celery_app.py` — Celery app configuration
- `backend/app/jobs/tasks.py` — 7 pipeline tasks

## Architecture

### Celery Configuration (`celery_app.py`)
- Broker: Redis (REDIS_URL)
- Backend: Redis (REDIS_URL)
- Serializer: JSON
- Settings: task_acks_late=True, worker_prefetch_multiplier=1

### Pipeline Tasks (PRD 9.1)

| Task | Name | Stage | Description |
|------|------|-------|-------------|
| 1 | validate_url_task | VALIDATING | SSRF validation of website_url |
| 2 | discover_pages_task | DISCOVERING | Sitemap + BFS page discovery |
| 3 | crawl_pages_task | CRAWLING | HTTP + Playwright concurrent crawl |
| 4 | extract_and_brand_task | EXTRACTING/BRANDING | Content extraction + brand heuristics |
| 5 | compile_knowledge_task | GENERATING_KNOWLEDGE | Build website.md canonical document |
| 6 | chunk_and_embed_task | CHUNKING/EMBEDDING/INDEXING | Chunk → embed → store vectors |
| 7 | finalize_crawl_task | COMPLETED | Set bot READY/READY_WITH_WARNINGS/FAILED |

### Task Chain
```python
chain(
    validate_url_task.si(bot_id, crawl_job_id),
    discover_pages_task.s(),
    crawl_pages_task.s(),
    extract_and_brand_task.s(),
    compile_knowledge_task.s(),
    chunk_and_embed_task.s(),
    finalize_crawl_task.s(),
).apply_async()
```

### State Machine
- Bot transitions: PENDING → CRAWLING → READY / READY_WITH_WARNINGS / FAILED
- CrawlJob transitions: QUEUED → RUNNING → COMPLETED / FAILED
- On any task failure: job.status=FAILED, bot.status=FAILED, error captured

### DB Access Strategy
- Celery workers use synchronous SQLAlchemy sessions (SYNC_DATABASE_URL)
- Async service functions called via asyncio.run() bridge

## Bot Status Finalization Logic
- chunk_count > 0 and failed_pages == 0 → READY
- chunk_count > 0 and failed_pages > 0 → READY_WITH_WARNINGS
- chunk_count == 0 → FAILED
