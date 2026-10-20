## 2024-05-19 - Concurrent SQLAlchemy Async Queries
**Learning:** A single `AsyncSession` injected into a FastAPI route cannot execute multiple queries concurrently via `asyncio.gather()`. It throws an `IllegalStateChangeError`.
**Action:** When parallelizing multiple read-only queries in FastAPI analytics endpoints, import `AsyncSessionLocal` and spawn separate context managers (`async with AsyncSessionLocal():`) for each query inside a task wrapper, then gather those tasks.
## 2024-10-20 - Consolidating Concurrent Queries
**Learning:** To avoid the issue of multiple database roundtrips and connection pool exhaustion when needing multiple count operations in SQLAlchemy, we can combine concurrent scalar counts into a single query using `scalar_subquery().label()` instead of executing them separately.
**Action:** Use `scalar_subquery().label()` within a single `select()` statement to fetch multiple aggregate values or related properties efficiently, reducing load on the database connection pool.
