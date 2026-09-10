# EmbedIQ backend

The backend is a FastAPI application that provides authentication, bot
management, crawling, knowledge ingestion, retrieval-augmented chat, widget
endpoints, and analytics.

## Main components

- `app/api/v1/`: versioned HTTP routes
- `app/models/`: SQLAlchemy models for users, bots, documents, chunks,
  conversations, and crawl jobs
- `app/services/`: crawling, extraction, chunking, embeddings, retrieval, and
  LLM orchestration
- `app/jobs/`: Celery application and background ingestion tasks
- `migrations/`: Alembic migrations
- `tests/`: API, service, security, and tenant-isolation tests

## Local development

From the repository root, start PostgreSQL/pgvector and Redis:

```bash
docker compose up -d postgres redis
```

Create a Python environment and install dependencies:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Apply migrations and run the API:

```bash
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

Run the Celery worker in another terminal:

```bash
celery -A app.jobs.celery_app worker --loglevel=info -c 4
```

The application reads configuration from the repository `.env` file through
`pydantic-settings`. Use `.env.example` as the starting point and provide
real values only in local or deployment secret storage.

## Database migrations

Create a migration after changing models:

```bash
alembic revision --autogenerate -m "describe the schema change"
```

Review generated SQL before applying it:

```bash
alembic upgrade head
```

## Tests

```bash
pytest
pytest tests/test_rag.py tests/test_retrieval.py
```

The test suite includes SSRF protections, rate limiting, authentication,
tenant isolation, ingestion, retrieval, and chat integration coverage.
