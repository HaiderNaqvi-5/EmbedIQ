## 2024-05-24 - Database Connection Pool Exhaustion in Analytics Endpoint
**Learning:** Combining multiple independent scalar queries (e.g. `func.count()`) that were previously executed concurrently via `asyncio.gather()` into a single query using `scalar_subquery().label()` significantly reduces database connection usage.
**Action:** When gathering multiple counts or simple scalars from the database within an endpoint, combine them into one `select` rather than spinning up concurrent `AsyncSession`s for each.
