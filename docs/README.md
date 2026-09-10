# EmbedIQ engineering documentation

This directory contains concise operational notes for contributors. Product
requirements and detailed design decisions remain in [`Doc & prd/`](../Doc%20%26%20prd/).

## System flow

1. A user creates a bot in the dashboard.
2. The API validates the target URL and schedules a crawl.
3. A Celery worker fetches pages, extracts readable content, chunks documents,
   and creates embeddings.
4. PostgreSQL with pgvector stores the tenant data and searchable chunks.
5. Chat requests retrieve relevant chunks and send grounded context to the
   configured LLM provider.
6. The dashboard and public widget consume the versioned API.

## Local services

| Service | Default address | Role |
| --- | --- | --- |
| Frontend | `http://localhost:3000` | Dashboard and widget |
| Backend | `http://localhost:8000` | FastAPI API |
| PostgreSQL/pgvector | `localhost:5433` | Relational and vector storage |
| Redis | `localhost:6379` | Celery broker, results, and rate limiting |

Start only the infrastructure with:

```bash
docker compose up -d postgres redis
```

## Contribution workflow

1. Create a focused branch.
2. Update models and an Alembic migration together.
3. Add or update backend tests for API and service behavior.
4. Run backend tests and the frontend build before opening a pull request.
5. Do not commit `.env`, generated dependencies, backups, database volumes, or
   build output.

## Related documents

- [Product requirements](../Doc%20%26%20prd/PRD.md)
- [Implementation baseline](../Doc%20%26%20prd/implementation.md)
- [Architecture sessions](../Doc%20%26%20prd/sessions/)
