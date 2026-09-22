## 2024-05-19 - Concurrent SQLAlchemy Async Queries
**Learning:** A single `AsyncSession` injected into a FastAPI route cannot execute multiple queries concurrently via `asyncio.gather()`. It throws an `IllegalStateChangeError`.
**Action:** When parallelizing multiple read-only queries in FastAPI analytics endpoints, import `AsyncSessionLocal` and spawn separate context managers (`async with AsyncSessionLocal():`) for each query inside a task wrapper, then gather those tasks.

## 2024-05-19 - [Combine concurrent DB scalar calls in FastAPI/SQLAlchemy]
**Learning:** Executing multiple scalar subqueries concurrently with `asyncio.gather` and separate DB sessions (e.g. `_execute_scalar`) consumes excessive connection pool resources and adds overhead, especially in FastAPI applications reporting analytics metrics.
**Action:** Always combine multiple single-value scalar subqueries into a single `select()` statement using `.scalar_subquery().label()` and execute them together in one session to optimize performance and prevent connection exhaustion.
