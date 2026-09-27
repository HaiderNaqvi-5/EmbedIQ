## 2024-05-19 - Concurrent SQLAlchemy Async Queries
**Learning:** A single `AsyncSession` injected into a FastAPI route cannot execute multiple queries concurrently via `asyncio.gather()`. It throws an `IllegalStateChangeError`.
**Action:** When parallelizing multiple read-only queries in FastAPI analytics endpoints, import `AsyncSessionLocal` and spawn separate context managers (`async with AsyncSessionLocal():`) for each query inside a task wrapper, then gather those tasks.
## 2024-06-03 - Optimizing concurrent scalar database counts
**Learning:** In the FastAPI backend, executing multiple concurrent scalar count queries using `asyncio.gather` on individual database connections can easily exhaust the pool (up to 8 connections at once per request). It is far more efficient to combine these scalar queries into a single query using `select(...).scalar_subquery().label(...)`.
**Action:** Always combine multiple concurrent database scalar lookups into a single SQL query via subqueries when possible, instead of firing off concurrent background tasks or grabbing multiple connections from the pool.
