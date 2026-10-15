## 2024-05-19 - Concurrent SQLAlchemy Async Queries
**Learning:** A single `AsyncSession` injected into a FastAPI route cannot execute multiple queries concurrently via `asyncio.gather()`. It throws an `IllegalStateChangeError`.
**Action:** When parallelizing multiple read-only queries in FastAPI analytics endpoints, import `AsyncSessionLocal` and spawn separate context managers (`async with AsyncSessionLocal():`) for each query inside a task wrapper, then gather those tasks.

## 2024-05-20 - Concurrent SQLAlchemy Subqueries
**Learning:** While using `asyncio.gather()` with multiple `AsyncSessionLocal()` context managers prevents `IllegalStateChangeError`, it significantly increases database connection checkouts and round trips.
**Action:** When calculating multiple scalar counts from the database, group them into a single query using `.scalar_subquery().label()` and fetch them in a single session to reduce connection pool exhaustion.
