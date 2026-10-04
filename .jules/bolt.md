## 2024-05-19 - Concurrent SQLAlchemy Async Queries
**Learning:** A single `AsyncSession` injected into a FastAPI route cannot execute multiple queries concurrently via `asyncio.gather()`. It throws an `IllegalStateChangeError`.
**Action:** When parallelizing multiple read-only queries in FastAPI analytics endpoints, import `AsyncSessionLocal` and spawn separate context managers (`async with AsyncSessionLocal():`) for each query inside a task wrapper, then gather those tasks.
## 2025-02-14 - Batching Scalar Subqueries for Backend Performance
**Learning:** In the FastAPI backend, executing multiple `SELECT COUNT(*)` queries concurrently using `asyncio.gather()` and individual `AsyncSessionLocal` instances can lead to database connection pool exhaustion and increased overhead.
**Action:** When multiple scalar aggregate counts are required for an endpoint (e.g. analytics), combine them into a single query using `.scalar_subquery().label("name")` and `select(q1, q2, ...)`. Execute this single query via `result = await session.execute(query)` and extract the values from `result.one()`.
