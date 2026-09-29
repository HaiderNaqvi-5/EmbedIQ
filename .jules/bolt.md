## 2024-05-19 - Concurrent SQLAlchemy Async Queries
**Learning:** A single `AsyncSession` injected into a FastAPI route cannot execute multiple queries concurrently via `asyncio.gather()`. It throws an `IllegalStateChangeError`.
**Action:** When parallelizing multiple read-only queries in FastAPI analytics endpoints, import `AsyncSessionLocal` and spawn separate context managers (`async with AsyncSessionLocal():`) for each query inside a task wrapper, then gather those tasks.

## 2024-06-25 - Combined SQLAlchemy Scalar Subqueries
**Learning:** For multiple concurrent analytics count queries, a single query using `scalar_subquery().label()` is far more efficient than parallel `_execute_scalar` sessions gathered via `asyncio.gather()`, as it only checks out one DB connection instead of ~8, preventing pool exhaustion.
**Action:** When a dashboard or analytics endpoint executes many `SELECT COUNT` queries, combine them into a single `select(subq1.label("a"), subq2.label("b"))` block to execute as a single network roundtrip.
