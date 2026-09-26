## 2024-05-19 - Concurrent SQLAlchemy Async Queries
**Learning:** A single `AsyncSession` injected into a FastAPI route cannot execute multiple queries concurrently via `asyncio.gather()`. It throws an `IllegalStateChangeError`.
**Action:** When parallelizing multiple read-only queries in FastAPI analytics endpoints, import `AsyncSessionLocal` and spawn separate context managers (`async with AsyncSessionLocal():`) for each query inside a task wrapper, then gather those tasks.

## 2024-05-20 - Combining Concurrent SQLAlchemy Scalar Queries
**Learning:** While spawning separate `AsyncSessionLocal` context managers allows concurrent execution of queries without `IllegalStateChangeError`, executing many (e.g., 8) simple scalar count queries concurrently can exhaust the database connection pool and adds unnecessary network overhead.
**Action:** To optimize multiple scalar count queries that don't depend on each other, combine them into a single query using `select(...)` with `.scalar_subquery().label()` for each count, executing it via a single session connection.
