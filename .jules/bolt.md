## 2024-05-19 - Concurrent SQLAlchemy Async Queries
**Learning:** A single `AsyncSession` injected into a FastAPI route cannot execute multiple queries concurrently via `asyncio.gather()`. It throws an `IllegalStateChangeError`.
**Action:** When parallelizing multiple read-only queries in FastAPI analytics endpoints, import `AsyncSessionLocal` and spawn separate context managers (`async with AsyncSessionLocal():`) for each query inside a task wrapper, then gather those tasks.

## 2024-05-19 - Concurrent SQLAlchemy Async Queries using Scalar Subqueries
**Learning:** Instead of using `asyncio.gather()` to run multiple separate `scalar` queries concurrently (which requires opening multiple database sessions to avoid `IllegalStateChangeError`), multiple `count` queries can be combined into a single query using `.scalar_subquery().label()`.
**Action:** When needing multiple simple counts or scalars in SQLAlchemy, combine them into one `select()` with labeled scalar subqueries to reduce database round-trips and connection pool usage.
