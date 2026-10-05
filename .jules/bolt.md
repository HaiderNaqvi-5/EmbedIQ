## 2024-05-19 - Concurrent SQLAlchemy Async Queries
**Learning:** A single `AsyncSession` injected into a FastAPI route cannot execute multiple queries concurrently via `asyncio.gather()`. It throws an `IllegalStateChangeError`.
**Action:** When parallelizing multiple read-only queries in FastAPI analytics endpoints, import `AsyncSessionLocal` and spawn separate context managers (`async with AsyncSessionLocal():`) for each query inside a task wrapper, then gather those tasks.

## 2024-10-05 - Optimizing Dashboard Analytics Queries
**Learning:** Analytics dashboard endpoints often spawn multiple scalar count queries (e.g., total users, total messages) using `asyncio.gather` with separate DB sessions. This quickly exhausts connection pools under moderate load.
**Action:** Always combine related scalar aggregation queries into a single query using `scalar_subquery().label()` and return them in one database roundtrip.
