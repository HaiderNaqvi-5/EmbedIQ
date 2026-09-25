## 2024-05-19 - Concurrent SQLAlchemy Async Queries
**Learning:** A single `AsyncSession` injected into a FastAPI route cannot execute multiple queries concurrently via `asyncio.gather()`. It throws an `IllegalStateChangeError`.
**Action:** When parallelizing multiple read-only queries in FastAPI analytics endpoints, import `AsyncSessionLocal` and spawn separate context managers (`async with AsyncSessionLocal():`) for each query inside a task wrapper, then gather those tasks.
## 2024-05-20 - Connection Pool Exhaustion from Concurrent Scalars
**Learning:** In the async FastAPI backend, using `asyncio.gather()` to concurrently execute multiple scalar subqueries (like `COUNT()`) forces SQLAlchemy to open a separate database connection from the pool for each query. In high-traffic endpoints (like analytics dashboards), this rapidly exhausts the connection pool.
**Action:** Combine multiple independent scalar counts into a single query using `.scalar_subquery().label()` within a master `select()`. This retrieves all values in a single database round-trip, utilizing only one connection.
