# EmbedIQ — Current Implementation State

Last Updated: 2026-09-09

## Overall Status

**All 9 Milestones are COMPLETE.** The EmbedIQ MVP is fully implemented: Modular Monolith (FastAPI + Celery + PostgreSQL/pgvector + Next.js 14) with 195 passing tests covering unit, integration, and acceptance levels.

---

## Component Implementation Status

### 1. Foundation & Infrastructure
* **Status**: COMPLETE
* **Implemented**:
  - Docker Compose (`pgvector/pgvector:pg16` on host port 5433, `redis:7-alpine` on port 6379, Backend, Celery worker).
  - Environment configuration (`.env.example`, `.env`, `.gitignore`).
  - FastAPI application scaffold with CORS, error envelope handlers, and `GET /api/health`.
  - SQLAlchemy 2.0 async engine (`asyncpg`) and session dependency.
  - All 8 database models with foreign key cascades and pgvector vector column (`User`, `Bot`, `CrawlJob`, `Page`, `Document`, `Chunk`, `BrandSettings`, `Conversation`, `Message`).
  - Alembic async migrations setup and initial schema migration applied.
  - Next.js 14 App Router frontend scaffold with Tailwind CSS, TypeScript, and Lucide icons.
  - Pytest test suite with model graph, cascading deletion, and pgvector cosine similarity tests.
* **Detailed history**: `sessions/foundation.md`

### 2. Authentication & Identity
* **Status**: COMPLETE
* **Implemented**:
  - `POST /api/auth/register` — user registration with password hashing (bcrypt via passlib).
  - `POST /api/auth/login` — JWT access token issuance (HS256).
  - `GET /api/auth/me` — authenticated profile endpoint.
  - `GET /api/bots`, `POST /api/bots`, `GET /api/bots/{bot_id}`, `DELETE /api/bots/{bot_id}` — full Bot CRUD with strict owner verification.
  - Pydantic request/response schemas for all auth and bot endpoints.
* **Detailed history**: `sessions/auth.md`

### 3. Website Intelligence (SSRF Guard & Crawler)
* **Status**: COMPLETE
* **Implemented**:
  - Pre-connection SSRF validation — IP range checks (RFC 1918, loopback, link-local, cloud metadata), scheme restriction (HTTP/HTTPS only), credential embedding rejection, hostname suffix blocking.
  - DNS resolution validation via `socket.getaddrinfo`.
  - URL normalization — fragment stripping, utm_* parameter removal, www-variant equivalence, asset URL detection.
  - Crawler integration via `httpx.AsyncClient` with configurable timeouts.
* **Detailed history**: `sessions/ssrf.md`

### 4. Knowledge Pipeline & Vector Store
* **Status**: COMPLETE
* **Implemented**:
  - Canonical `website.md` generator (`knowledge_builder.py`) — YAML frontmatter (bot_id, crawl_job_id, website_url, website_name, timestamps) + per-page sections with source URLs and titles.
  - Markdown-aware semantic chunking (`chunker.py`) — heading-aware split, 600-1000 token target per chunk, oversized paragraph splitting, sequential chunk indices, page boundary isolation.
  - Embedding service abstraction (`embedding_service.py`) — OpenAI `text-embedding-3-small` / `bge-small` via `get_embedding_provider()`, batched embedding with configurable batch size, MockEmbeddingProvider for tests.
  - PostgreSQL pgvector HNSW index for vector similarity search.
* **Detailed history**: `sessions/knowledge.md`

### 5. AI & Guarded RAG Engine
* **Status**: COMPLETE
* **Implemented**:
  - Bot-scoped vector retrieval (`retrieval.py`) — `WHERE bot_id = :bot_id` filtering, top_k limiting, embedding similarity search.
  - Guarded XML prompt construction (`rag.py`) — system prompt with anti-hallucination rules, XML-formatted context blocks, source deduplication, out-of-scope guard fallback.
  - LLM service abstraction (`llm_service.py`) — OpenAI provider with streaming, MockLLMProvider for tests, factory selection via `get_llm_provider()`.
  - SSE streaming chat endpoint (`POST /api/chat/stream`).
* **Detailed history**: `sessions/rag.md`

### 6. Background Task Pipeline (Celery)
* **Status**: COMPLETE
* **Implemented**:
  - Celery workflow: `validate` → `discover` → `crawl` → `extract` → `brand` → `knowledge` → `chunk_embed` → `finalize`.
  - Bot creation dispatches background crawl pipeline via `BackgroundTasks`.
  - Crawl job progress tracking and state transitions.
* **Detailed history**: `sessions/celery.md`

### 7. Product Frontend Dashboard
* **Status**: COMPLETE
* **Implemented**:
  - Next.js 14 App Router dashboard with bot management.
  - Bot creation wizard, real-time crawl visualizer.
  - Markdown knowledge inspector, live chat preview.
* **Detailed history**: `sessions/frontend.md`

### 8. Branding & Embeddable Widget
* **Status**: COMPLETE
* **Implemented**:
  - Heuristic branding extraction (`extractor.py`) — logo from apple-touch-icon, primary color from CSS variables, company name from og:site_name with fallback to title, confidence scores.
  - Brand settings CRUD (`POST/GET/PATCH /api/bots/{bot_id}/brand`).
  - Public widget configuration endpoint (`GET /api/widget/config/{bot_id}`) — no auth required.
  - Standalone `<15KB` `widget.js` loader.
  - Hosted iframe React chat UI.
* **Detailed history**: `sessions/widget.md`

### 9. Hardening & End-to-End Test Suite
* **Status**: COMPLETE
* **Implemented**:
  - In-memory sliding-window rate limiter middleware — 60 req/min on chat endpoints, 5 bot creations/hr per user.
  - `Retry-After`, `X-RateLimit-Limit`, `X-RateLimit-Remaining` headers on 429 responses.
  - 195-test suite covering: SSRF guard, chunker, vector retrieval, RAG engine, knowledge builder, extractor, LLM service, embedding service, chat integration, tenant isolation, rate limiting, and full acceptance tests (AT-001 through AT-010).
  - Test infrastructure fix: savepoint-based `db_session` fixture enabling endpoint commits within tests.
* **Detailed history**: `sessions/hardening.md`

---

## Current System Flow

```
[Docker: Postgres (pgvector) + Redis]
               │
               ▼
[FastAPI Backend] ──(asyncpg)──► [PostgreSQL: All Models + HNSW Vector Index]
       │
       ├──► [Auth API] ── JWT Bearer verification
       ├──► [Bot CRUD API] ── Owner verification
       ├──► [Chat API] ── Bot readiness guard → Rate limit → RAG → SSE streaming
       ├──► [Widget Config API] ── Public endpoint, no auth
       ├──► [SSRF Guard] ── Pre-connection validation
       └──► [Celery Worker] ── Crawl pipeline (validate→discover→crawl→extract→brand→knowledge→chunk_embed→finalize)
               │
       [Next.js 14 Frontend] ── Dashboard + Live Chat Preview
       [Embeddable Widget] ── <15KB widget.js + iframe React UI
```

---

## Remaining MVP Requirements

**None — All milestones complete.**

---

## Current Blockers

None.

---

## Session Documentation

* PRD, Architecture & Rules Setup → `sessions/prd_and_architecture.md`
* Milestone 1: Foundation & Scaffold → `sessions/foundation.md`
* Milestone 2: Authentication & Bot Management → `sessions/auth.md`
* Milestone 3: SSRF Guard & Website Intelligence → `sessions/ssrf.md`
* Milestone 4: Knowledge Pipeline & Vector Store → `sessions/knowledge.md`
* Milestone 5: Guarded RAG Engine & SSE Streaming → `sessions/rag.md`
* Milestone 6: Celery Background Job Pipeline → `sessions/celery.md`
* Milestone 7: Frontend Dashboard & Live Preview → `sessions/frontend.md`
* Milestone 8: Branding & Embeddable Widget → `sessions/widget.md`
* Milestone 9: Hardening & End-to-End Test Suite → `sessions/hardening.md`
