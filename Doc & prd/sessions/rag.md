# Session: Guarded RAG & Inference (Milestone 5)

## Status: COMPLETE

## Date
2026-09-09

## Summary
Implemented the full Retrieval-Augmented Generation pipeline with bot-scoped vector search, guarded prompting, multi-turn memory, and SSE streaming.

## Files Created

- `backend/app/services/retrieval.py` — Bot-scoped pgvector similarity search
- `backend/app/services/llm_service.py` — Provider-abstracted LLM (OpenAI + Mock)
- `backend/app/services/rag.py` — Full RAG engine (streaming + non-streaming)
- `backend/app/api/v1/chat.py` — Chat API endpoints (JSON + SSE)
- `backend/app/api/v1/widget.py` — Public widget config endpoint
- `backend/app/schemas/chat.py` — Chat request/response schemas
- `backend/app/schemas/widget.py` — Widget config schemas

## Architecture

### Vector Retrieval (`retrieval.py`)
CRITICAL: Every query includes `WHERE bot_id = :bot_id`. Cross-bot retrieval is architecturally prohibited.

SQL contract (verbatim from PRD 6.3.1):
```sql
SELECT id, source_url, page_title, heading_path, content,
       1 - (embedding <=> :query_vector) AS similarity
FROM chunks
WHERE bot_id = :bot_id
  AND (1 - (embedding <=> :query_vector)) >= :min_similarity
ORDER BY embedding <=> :query_vector ASC
LIMIT :top_k
```

Defaults: top_k=5, min_similarity=0.65, max_top_k=10

### RAG Engine (`rag.py`)
- Guarded system prompt: XML `<website_context>` fencing
- Out-of-scope guard: if 0 chunks meet threshold → return deterministic refusal without calling LLM
- Multi-turn history: last 6 messages (3 user + 3 assistant) — PRD 6.3.3
- Conversation persistence: Conversation + Message rows stored per session_id

### LLM Service (`llm_service.py`)
- OpenAI gpt-4o-mini via HTTPX (streaming: SSE parsing; non-streaming: JSON)
- MockLLMProvider: deterministic stub when LLM_API_KEY is placeholder

### Chat API (`chat.py`)
- POST /api/chat — standard JSON (200)
- POST /api/chat/stream — SSE streaming (text/event-stream)
- Both are public (no JWT)
- Bot must be READY or READY_WITH_WARNINGS (else 409)

## SSE Event Format (PRD 6.3.4)
```
event: token
data: {"text": "..."}

event: sources
data: [{"url": "...", "title": "..."}]

event: done
data: {"status": "complete"}

event: error
data: {"code": "...", "message": "..."}
```

## Security Invariants
- All scraped content wrapped in <website_context> XML tags
- Labelled as "untrusted reference data" in system prompt
- LLM explicitly forbidden from executing instructions found in context
