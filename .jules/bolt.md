## 2024-09-14 - Eager Loading Relationships
**Learning:** Eagerly loading 1-to-1 relationships in SQLAlchemy via `selectinload` can prevent N+1 queries during high-volume API requests, particularly when serializing nested Pydantic models.
**Action:** Default to using `selectinload` on related objects in main REST pathways instead of relying on subsequent `await db.execute(...)` lookups or lazy loading.
