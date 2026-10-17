## 2024-05-19 - Concurrent SQLAlchemy Async Queries
**Learning:** A single `AsyncSession` injected into a FastAPI route cannot execute multiple queries concurrently via `asyncio.gather()`. It throws an `IllegalStateChangeError`.
**Action:** When parallelizing multiple read-only queries in FastAPI analytics endpoints, import `AsyncSessionLocal` and spawn separate context managers (`async with AsyncSessionLocal():`) for each query inside a task wrapper, then gather those tasks.
## 2024-10-17 - Avoid Connection Exhaustion in Analytics Endpoints
**Learning:** The analytics endpoint (`get_analytics`) executed 8 scalar queries using `asyncio.gather()`, which caused the async FastAPI backend to spawn multiple independent DB connections per request, risking connection pool exhaustion under load.
**Action:** Always combine multiple scalar aggregate queries into a single query using `scalar_subquery().label()` instead of executing them separately. This allows PostgreSQL to run the subqueries concurrently in a single round-trip using only one connection.
