## 2024-05-19 - Concurrent SQLAlchemy Async Queries
**Learning:** A single `AsyncSession` injected into a FastAPI route cannot execute multiple queries concurrently via `asyncio.gather()`. It throws an `IllegalStateChangeError`.
**Action:** When parallelizing multiple read-only queries in FastAPI analytics endpoints, import `AsyncSessionLocal` and spawn separate context managers (`async with AsyncSessionLocal():`) for each query inside a task wrapper, then gather those tasks.
## 2024-10-01 - Optimizing Concurrent SQLAlchemy Counts
**Learning:** In the async FastAPI backend, executing multiple `COUNT` queries concurrently via `asyncio.gather` with separate sessions (`AsyncSessionLocal`) works but uses many database connections and adds network overhead.
**Action:** When calculating dashboard summaries involving multiple scalar counts on related tables, combine them into a single query using `scalar_subquery().label()` and execute it with a single `session.execute(query).first()` to improve performance and prevent connection pool exhaustion.
