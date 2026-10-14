## 2024-05-19 - Concurrent SQLAlchemy Async Queries
**Learning:** A single `AsyncSession` injected into a FastAPI route cannot execute multiple queries concurrently via `asyncio.gather()`. It throws an `IllegalStateChangeError`.
**Action:** When parallelizing multiple read-only queries in FastAPI analytics endpoints, import `AsyncSessionLocal` and spawn separate context managers (`async with AsyncSessionLocal():`) for each query inside a task wrapper, then gather those tasks.

## 2024-05-18 - Avoiding Database Connection Pool Exhaustion in Analytics
**Learning:** Using `asyncio.gather` on multiple independent `_execute_scalar` calls creates an equal number of `AsyncSessionLocal` database connections, rapidly exhausting the worker connection pool on dashboard load.
**Action:** Always bundle multiple scalar queries into a single combined query using `scalar_subquery().label()` to execute as one database transaction and consume only one pool connection.
