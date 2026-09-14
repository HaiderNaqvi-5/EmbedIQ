## 2024-05-19 - Fast Upsert with IN clause
**Learning:** Using an IN clause to fetch all existing records by a list of identifying fields (like URLs) and storing them in a dictionary mapping before a loop is over 40x faster than doing individual `SELECT ... WHERE ...` inside the loop (N+1 query problem) in SQLAlchemy.
**Action:** Next time I need to insert/update a large list of items, pre-fetch all existing items in a single query outside the loop using an IN clause to map them for O(1) lookups.
