## 2024-05-19 - Concurrent SQLAlchemy Async Queries
**Learning:** A single `AsyncSession` injected into a FastAPI route cannot execute multiple queries concurrently via `asyncio.gather()`. It throws an `IllegalStateChangeError`.
**Action:** When parallelizing multiple read-only queries in FastAPI analytics endpoints, import `AsyncSessionLocal` and spawn separate context managers (`async with AsyncSessionLocal():`) for each query inside a task wrapper, then gather those tasks.
## 2024-05-19 - N+1 Queries in Chat API
**Learning:** The chat and chat stream endpoints were executing multiple queries to resolve the bot and its branding settings (an N+1 pattern).
**Action:** Use SQLAlchemy's `joinedload` on relationships (like `Bot.brand_settings`) to eagerly fetch related data in a single query when that data is immediately needed.
