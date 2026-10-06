## 2024-05-19 - Concurrent SQLAlchemy Async Queries
**Learning:** A single `AsyncSession` injected into a FastAPI route cannot execute multiple queries concurrently via `asyncio.gather()`. It throws an `IllegalStateChangeError`.
**Action:** When parallelizing multiple read-only queries in FastAPI analytics endpoints, import `AsyncSessionLocal` and spawn separate context managers (`async with AsyncSessionLocal():`) for each query inside a task wrapper, then gather those tasks.
## 2024-10-06 - Consolidating Concurrent Scalar Subqueries
**Learning:** Even when correctly using separate `AsyncSessionLocal` contexts to avoid `IllegalStateChangeError` in `asyncio.gather()`, running multiple scalar queries concurrently still exhausts connection pools under load and adds unnecessary latency via DB roundtrips.
**Action:** When calculating multiple scalar aggregates on the same relationships or same endpoints (e.g., in analytics dashboards), use a single `select(...)` combined with multiple `.scalar_subquery().label(...)` to collapse them into a single database roundtrip.
