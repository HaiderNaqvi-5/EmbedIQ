## 2024-05-19 - Concurrent SQLAlchemy Async Queries
**Learning:** A single `AsyncSession` injected into a FastAPI route cannot execute multiple queries concurrently via `asyncio.gather()`. It throws an `IllegalStateChangeError`.
**Action:** When parallelizing multiple read-only queries in FastAPI analytics endpoints, import `AsyncSessionLocal` and spawn separate context managers (`async with AsyncSessionLocal():`) for each query inside a task wrapper, then gather those tasks.

## 2024-05-18 - Avoid Concurrent SQLAlchemy scalar queries leading to connection pool exhaustion
**Learning:** Using `asyncio.gather()` to concurrently execute multiple isolated scalar count queries via FastAPI's `AsyncSessionLocal` effectively consumes an equal number of database connections, causing connection pool exhaustion and database strain.
**Action:** Always combine concurrent analytical scalar subqueries into a single query using `scalar_subquery().label()` instead of parallel independent connections. This minimizes query parsing overhead and network latency.
