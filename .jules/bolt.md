## 2024-05-19 - Concurrent SQLAlchemy Async Queries
**Learning:** A single `AsyncSession` injected into a FastAPI route cannot execute multiple queries concurrently via `asyncio.gather()`. It throws an `IllegalStateChangeError`.
**Action:** When parallelizing multiple read-only queries in FastAPI analytics endpoints, import `AsyncSessionLocal` and spawn separate context managers (`async with AsyncSessionLocal():`) for each query inside a task wrapper, then gather those tasks.
## 2024-09-30 - Prevent Connection Pool Exhaustion in FastAPI

**Learning:** When executing multiple concurrent `SELECT COUNT(...)` queries using `asyncio.gather()` in FastAPI with SQLAlchemy, opening a new `AsyncSessionLocal()` connection for each query can rapidly lead to connection pool exhaustion under load.

**Action:** Combine multiple independent scalar counts into a single row output using `scalar_subquery().label("name")`. This fetches all the aggregates in a single roundtrip while only tying up a single database connection.
