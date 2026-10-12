## 2024-05-19 - Concurrent SQLAlchemy Async Queries
**Learning:** A single `AsyncSession` injected into a FastAPI route cannot execute multiple queries concurrently via `asyncio.gather()`. It throws an `IllegalStateChangeError`.
**Action:** When parallelizing multiple read-only queries in FastAPI analytics endpoints, import `AsyncSessionLocal` and spawn separate context managers (`async with AsyncSessionLocal():`) for each query inside a task wrapper, then gather those tasks.

## 2023-10-24 - SQLAlchemy AsyncSession Gather Exhaustion
**Learning:** In the FastAPI backend, doing multiple `.scalar_one()` queries via `asyncio.gather()` opens multiple DB connections concurrently. Using `asyncio.gather()` with individual async sessions for 8 scalar COUNT queries causes connection pool starvation.
**Action:** Combine multiple scalar queries into a single query using `select(query1.scalar_subquery().label("name1"), query2.scalar_subquery().label("name2"))` and unpack using `result.first()` to save overhead and connections.
