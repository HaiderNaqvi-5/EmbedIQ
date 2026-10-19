## 2024-05-19 - Concurrent SQLAlchemy Async Queries
**Learning:** A single `AsyncSession` injected into a FastAPI route cannot execute multiple queries concurrently via `asyncio.gather()`. It throws an `IllegalStateChangeError`.
**Action:** When parallelizing multiple read-only queries in FastAPI analytics endpoints, import `AsyncSessionLocal` and spawn separate context managers (`async with AsyncSessionLocal():`) for each query inside a task wrapper, then gather those tasks.

## 2024-10-19 - Concurrent SQLAlchemy Async Queries using Subqueries
**Learning:** A single `AsyncSession` injected into a FastAPI route cannot execute multiple queries concurrently via `asyncio.gather()`. While spawning separate `AsyncSessionLocal` instances is one workaround, combining multiple scalar queries into a single large query using `.scalar_subquery().label(...)` is vastly superior for performance as it requires only a single database connection and round trip.
**Action:** When querying multiple independent scalars (like dashboard counts), combine them into a single `select(...)` query using scalar subqueries instead of parallelizing them with multiple database connections.
