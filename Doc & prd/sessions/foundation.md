# Feature: Milestone 1 — Foundation & Scaffold

## Current Status

COMPLETE

## Objective

Establish the initial infrastructure, root configuration, backend FastAPI asynchronous service layer, PostgreSQL + pgvector database models & migrations, and Next.js 14 App Router frontend baseline.

## Work Completed

1. **Root Infrastructure**:
   - Created `.gitignore` ignoring build artifacts, virtual environments, node modules, and secrets.
   - Created `.env.example` and local `.env` with full configuration parameters (database, redis, JWT, AI providers, crawler limits).
   - Created `docker-compose.yml` with `pgvector/pgvector:pg16` (port mapped to 5433:5432 to prevent local port collisions), `redis:7-alpine`, FastAPI backend, and Celery worker.
2. **Backend Scaffolding (`backend/`)**:
   - Configured `pyproject.toml`, `requirements.txt`, and `Dockerfile`.
   - Implemented `app/core/config.py` with Pydantic v2 `Settings`.
   - Implemented `app/db/base.py` and `app/db/session.py` with async SQLAlchemy 2.0 (`asyncpg`).
   - Implemented all 8 SQLAlchemy ORM models with strict PRD schemas, foreign key cascades, and pgvector vector column:
     - `User` (`app/models/user.py`)
     - `Bot` (`app/models/bot.py`)
     - `CrawlJob` (`app/models/crawl_job.py`)
     - `Page` (`app/models/page.py`)
     - `Document` (`app/models/document.py`)
     - `Chunk` (`app/models/chunk.py`)
     - `BrandSettings` (`app/models/brand.py`)
     - `Conversation` & `Message` (`app/models/conversation.py`)
   - Implemented `app/main.py` with CORS, standard error envelope handlers, and `GET /api/health`.
   - Configured Alembic async migrations (`alembic.ini`, `migrations/env.py`, `migrations/versions/001_initial_schema.py`) and executed migration successfully against PostgreSQL + pgvector.
3. **Frontend Scaffolding (`frontend/`)**:
   - Initialized Next.js 14 App Router project with TypeScript, Tailwind CSS, Lucide icons.
   - Implemented `app/layout.tsx`, `app/globals.css`, and `app/page.tsx` landing page.
   - Verified production build (`npm run build`).
4. **Testing Suite**:
   - Implemented pytest fixtures in `tests/conftest.py` with isolated session rollbacks.
   - Implemented `tests/test_health.py` and `tests/test_db_models.py` verifying full entity graph, cascading deletion, and pgvector cosine similarity calculation.

## Files Created

- `.gitignore` — Root git ignore.
- `.env.example` — Environment template.
- `.env` — Local development environment config.
- `docker-compose.yml` — Multi-container setup for Postgres+pgvector, Redis, Backend, Celery.
- `backend/Dockerfile` — Backend container image definition.
- `backend/pyproject.toml` — Python project configuration.
- `backend/requirements.txt` — Python dependencies.
- `backend/app/core/config.py` — Settings and operational limits.
- `backend/app/db/base.py` — Declarative base and timestamp mixins.
- `backend/app/db/session.py` — Async SQLAlchemy engine & session factory.
- `backend/app/models/user.py` — User model.
- `backend/app/models/bot.py` — Bot model.
- `backend/app/models/crawl_job.py` — CrawlJob model.
- `backend/app/models/page.py` — Page model.
- `backend/app/models/document.py` — Document model.
- `backend/app/models/chunk.py` — Chunk model with pgvector Vector(1536).
- `backend/app/models/brand.py` — BrandSettings model.
- `backend/app/models/conversation.py` — Conversation & Message models.
- `backend/app/models/__init__.py` — Models package export.
- `backend/app/main.py` — FastAPI application.
- `backend/alembic.ini` — Alembic config.
- `backend/migrations/env.py` — Async Alembic environment.
- `backend/migrations/script.py.mako` — Migration template.
- `backend/migrations/versions/001_initial_schema.py` — Initial DDL migration.
- `backend/tests/conftest.py` — Pytest fixtures.
- `backend/tests/test_health.py` — Health endpoint tests.
- `backend/tests/test_db_models.py` — Database model relationship and vector tests.
- `frontend/package.json` — Frontend dependencies.
- `frontend/tsconfig.json` — TypeScript config.
- `frontend/tailwind.config.ts` — Tailwind config.
- `frontend/postcss.config.js` — PostCSS config.
- `frontend/next.config.js` — Next.js config with API rewrites.
- `frontend/app/globals.css` — Global CSS styling.
- `frontend/app/layout.tsx` — Root layout.
- `frontend/app/page.tsx` — Homepage landing view.

## Files Modified

None.

## Implementation Details

- **PostgreSQL + pgvector**: Running in container `embediq-postgres` on port 5433. Database extension `vector` is enabled. HNSW index created on `chunks.embedding` using `vector_cosine_ops` (`m=16, ef_construction=64`).
- **Cascade Rules**: Deleting a `User` cascades to `Bot`, which cascades to `CrawlJob`, `Page`, `Document`, `Chunk`, `BrandSettings`, and `Conversation`.
- **Error Envelopes**: Global FastAPI handlers return structured JSON matching `{"error": {"code": "...", "message": "...", "request_id": "..."}}`.

## Important Decisions

- Mapped postgres container port to `5433:5432` to avoid conflicts with host PostgreSQL on default port 5432.
- Used Python 3.11 with `uv` for package resolution.

## PRD References

- Section 5: Confirmed Technology Stack & Infrastructure
- Section 7: Complete Database Schema & Entity Relationships
- Section 8: Comprehensive REST & Streaming API Contract
- Section 10: Frontend & User Interface Architecture
- Section 13: Milestone 1 (Foundation)

## Problems Encountered

- Port 5432 was occupied by an existing local Postgres container. Resolved by mapping Docker container port to 5433 on the host while keeping internal network communication standard.
- Pytest asyncpg connection pooling required `NullPool` in test fixtures to guarantee clean per-test transactional isolation.

## Remaining Work

Proceed with **Milestone 2: Authentication & Bot Management**:
- Implement password hashing (bcrypt) and JWT utility in `app/core/security.py`.
- Implement user registration (`POST /api/auth/register`), login (`POST /api/auth/login`), and current user dependency (`get_current_user`).
- Implement Bot CRUD (`POST /api/bots`, `GET /api/bots`, `GET /api/bots/{bot_id}`).
- Implement ownership verification guard (`get_bot_for_user`).
- Implement auth and bot management tests.

## Testing Performed

1. `pytest backend/tests -v`
   - `test_create_user_and_bot` PASSED
   - `test_full_knowledge_and_chunk_graph` PASSED (verified 1536d vector cosine similarity)
   - `test_cascading_deletion` PASSED
   - `test_root_endpoint` PASSED
   - `test_health_check_endpoint` PASSED
2. `cd frontend && npm run build`
   - Compiled successfully, type check passed, static pages generated.

## Known Issues

None currently known.

## Next Recommended Step

Begin **Milestone 2: Authentication & Bot Management**.
