## 2024-05-19 - Concurrent SQLAlchemy Async Queries
**Learning:** A single `AsyncSession` injected into a FastAPI route cannot execute multiple queries concurrently via `asyncio.gather()`. It throws an `IllegalStateChangeError`.
**Action:** When parallelizing multiple read-only queries in FastAPI analytics endpoints, import `AsyncSessionLocal` and spawn separate context managers (`async with AsyncSessionLocal():`) for each query inside a task wrapper, then gather those tasks.
## 2024-05-19 - Concurrent SQLAlchemy Async Queries
**Learning:** A single `AsyncSession` injected into a FastAPI route cannot execute multiple queries concurrently via `asyncio.gather()`. It throws an `IllegalStateChangeError`.
**Action:** When parallelizing multiple read-only queries in FastAPI analytics endpoints, import `AsyncSessionLocal` and spawn separate context managers (`async with AsyncSessionLocal():`) for each query inside a task wrapper, then gather those tasks.

## 2024-05-20 - Reducing Database Connections for Concurrent Counts
**Learning:** Executing multiple aggregate counts (like dashboard analytics) concurrently with `asyncio.gather` and multiple independent `AsyncSessionLocal` instances consumes a significant number of active database connections from the connection pool (O(N) connections for N counts) and increases network overhead.
**Action:** Combine multiple independent scalar count queries into a single query block using SQLAlchemy's `.scalar_subquery().label(...)`. This allows retrieving all counts in a single database round-trip (O(1) connection) with significantly reduced latency and connection pool pressure.
