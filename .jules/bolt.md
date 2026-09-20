## 2024-05-19 - Concurrent SQLAlchemy Async Queries
**Learning:** A single `AsyncSession` injected into a FastAPI route cannot execute multiple queries concurrently via `asyncio.gather()`. It throws an `IllegalStateChangeError`.
**Action:** When parallelizing multiple read-only queries in FastAPI analytics endpoints, import `AsyncSessionLocal` and spawn separate context managers (`async with AsyncSessionLocal():`) for each query inside a task wrapper, then gather those tasks.
## 2024-05-19 - N+1 Queries in Concurrent Count Queries
**Learning:** The `get_analytics` endpoint suffered from executing multiple concurrent scalar count queries (`select(func.count(...))`) over independent connections in `asyncio.gather`, exhausting DB connection pool and causing high latency overhead for many isolated roundtrips.
**Action:** When calculating multiple aggregate counts, refactor them into scalar subqueries (`q.scalar_subquery().label(...)`) and combine them into a single `select(...)` query. This reduces N database roundtrips down to 1.
