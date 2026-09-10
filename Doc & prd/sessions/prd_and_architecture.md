# Feature: PRD, Architecture & Development Rules Baseline

## Current Status

COMPLETE

## Objective

Establish the authoritative Product Requirements Document (`PRD.md`), document and lock the project development rules (`PROJECT_RULES.md`), and initialize the baseline tracking structure (`implementation.md`) for EmbedIQ.

## Work Completed

1. Conducted an in-depth gap analysis of the original requirements specification.
2. Rewrote and structured the specification into a production-grade Product Requirements Document (`PRD.md`).
3. Added complete details for the confirmed technology stack (FastAPI, Next.js, Celery, Redis, PostgreSQL + `pgvector`, Playwright, BeautifulSoup4/lxml, `widget.js`).
4. Incorporated strict SSRF protection rules, HNSW index parameters, SSE streaming endpoint specifications, and complete SQL DDL with foreign key constraints.
5. Saved and locked the mandatory project development rules (`PROJECT_RULES.md`).
6. Initialized the project status map in `implementation.md`.

## Files Created

- `Doc & prd/PRD.md` — Authoritative locked specification and source of truth for the EmbedIQ platform.
- `Doc & prd/PROJECT_RULES.md` — Mandatory development rules, change procedures, documentation rules, and architectural invariants.
- `Doc & prd/implementation.md` — Current project implementation status and roadmap.
- `Doc & prd/sessions/prd_and_architecture.md` — Session record of PRD, architecture, and rules setup.

## Files Modified

None.

## Implementation Details

- Defined the 4 core product engines: Website Intelligence, Knowledge & Vectorization, Guarded RAG, and Embed Runtime.
- Documented the database schema across 8 entities (`users`, `bots`, `crawl_jobs`, `pages`, `documents`, `chunks`, `brand_settings`, `conversations`, `messages`).
- Established the 14-point Definition of Done checklist.

## Important Decisions

- **Architecture**: Modular monolith with FastAPI backend and Next.js frontend to minimize operational complexity while maintaining clean module boundaries.
- **Database**: PostgreSQL 15+ with `pgvector` extension using HNSW cosine index (`m=16, ef_construction=64`) to unify relational data and vector embeddings in a single ACID store.
- **SSRF Defense**: Strict pre-connection DNS resolution and private/internal IP blacklisting.

## PRD References

- Section 1: Document Control & Executive Summary
- Section 4: Core Architectural Principles & Invariants
- Section 5: Confirmed Technology Stack & Infrastructure
- Section 6: Product Engine Specifications
- Section 7: Complete Database Schema & Entity Relationships

## Problems Encountered

None.

## Remaining Work

Begin Milestone 1 (Foundation & Scaffold): Docker compose, backend/frontend folder scaffold, database models, and environment configuration.

## Testing Performed

- Verified file creation and markdown rendering across all files in `Doc & prd/`.

## Known Issues

None currently known.

## Next Recommended Step

Proceed with **Milestone 1: Foundation & Scaffold** (Setup repository structure, `docker-compose.yml`, backend/frontend baseline, and PostgreSQL+pgvector setup).
