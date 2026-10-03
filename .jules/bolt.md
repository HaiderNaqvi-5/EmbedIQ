## 2024-05-19 - Concurrent SQLAlchemy Async Queries
**Learning:** A single `AsyncSession` injected into a FastAPI route cannot execute multiple queries concurrently via `asyncio.gather()`. It throws an `IllegalStateChangeError`.
**Action:** When parallelizing multiple read-only queries in FastAPI analytics endpoints, import `AsyncSessionLocal` and spawn separate context managers (`async with AsyncSessionLocal():`) for each query inside a task wrapper, then gather those tasks.
## 2024-05-19 - Batched Scalar Queries via scalar_subquery()
**Learning:** To optimize DB connections and performance when fetching multiple scalar counts, using `.scalar_subquery().label("name")` inside a single `select(...)` is highly effective. It prevents connection pool exhaustion from spawning many parallel queries via `asyncio.gather()`.
**Action:** When needing multiple aggregate counts in analytics endpoints, combine them into one query instead of parallelizing individual sessions.
