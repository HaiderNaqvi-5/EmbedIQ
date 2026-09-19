## 2024-05-19 - Concurrent SQLAlchemy Async Queries
**Learning:** A single `AsyncSession` injected into a FastAPI route cannot execute multiple queries concurrently via `asyncio.gather()`. It throws an `IllegalStateChangeError`.
**Action:** When parallelizing multiple read-only queries in FastAPI analytics endpoints, import `AsyncSessionLocal` and spawn separate context managers (`async with AsyncSessionLocal():`) for each query inside a task wrapper, then gather those tasks.
## 2026-09-19 - Scalar Subqueries in Analytics
**Learning:** Correlated scalar subqueries in SQLAlchemy can lead to N+1 like performance issues and unnecessary multiple joins across tables when querying lists.
**Action:** When calculating counts or aggregates for a list of parent rows (like Bots with their Conversations and Messages), prefer using `outerjoin` and `group_by` with aggregation functions (e.g., `func.count(func.distinct(Conversation.id))`) to perform the calculation in a single pass.
