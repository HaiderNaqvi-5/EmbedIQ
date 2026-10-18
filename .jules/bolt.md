## 2024-05-19 - Concurrent SQLAlchemy Async Queries
**Learning:** A single `AsyncSession` injected into a FastAPI route cannot execute multiple queries concurrently via `asyncio.gather()`. It throws an `IllegalStateChangeError`.
**Action:** When parallelizing multiple read-only queries in FastAPI analytics endpoints, import `AsyncSessionLocal` and spawn separate context managers (`async with AsyncSessionLocal():`) for each query inside a task wrapper, then gather those tasks.
## 2024-05-18 - SQLAlchemy scalar_subquery() over multiple awaits
**Learning:** In the async FastAPI backend, executing multiple concurrent count queries using `await db.execute()` sequentially causes unnecessary database roundtrips, and using `asyncio.gather()` raises an `IllegalStateChangeError` due to connection pool limits. Combining counts into a single query using `scalar_subquery().label()` is much more efficient.
**Action:** When calculating multiple aggregates (like counts) for the same entity or related entities, always combine them into a single `select()` query using `scalar_subquery()` instead of multiple independent `await db.execute()` calls.
