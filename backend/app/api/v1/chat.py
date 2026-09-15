"""
Chat API Endpoints (PRD Section 8.3)
=====================================
Public endpoints — no JWT required. Bot identified by bot_id in request body.

  POST /api/chat         — Standard JSON response
  POST /api/chat/stream  — Server-Sent Events streaming response
"""

import json
import logging
import uuid
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.bot import Bot
from app.models.brand import BrandSettings
from app.schemas.chat import ChatRequest, ChatResponse, SourceRef
from app.services.rag import RAGRequest, chat_with_rag, stream_chat_with_rag

logger = logging.getLogger("embediq.chat")

router = APIRouter(prefix="/chat", tags=["Chat"])


async def _get_ready_bot(bot_id: uuid.UUID, db: AsyncSession) -> Bot:
    """Load the bot and verify it is in a ready state for chat.

    Raises HTTP 404 if the bot does not exist.
    Raises HTTP 409 if the bot has not finished indexing yet.
    """
    result = await db.execute(select(Bot).where(Bot.id == bot_id))
    bot = result.scalar_one_or_none()
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "BOT_NOT_FOUND", "message": "Bot not found"},
        )
    if bot.status not in ("READY", "READY_WITH_WARNINGS"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "BOT_NOT_READY",
                "message": f"Bot is not ready for chat (current status: {bot.status})",
            },
        )
    return bot


async def _get_bot_name(bot_id: uuid.UUID, db: AsyncSession) -> str:
    """Fetch the company_name from brand_settings (fallback to bot name)."""
    result = await db.execute(
        select(BrandSettings).where(BrandSettings.bot_id == bot_id)
    )
    brand = result.scalar_one_or_none()
    if brand and brand.company_name:
        return brand.company_name

    result2 = await db.execute(select(Bot).where(Bot.id == bot_id))
    bot = result2.scalar_one_or_none()
    return bot.name if bot else "the website assistant"


# ---------------------------------------------------------------------------
# POST /api/chat — Standard JSON chat
# ---------------------------------------------------------------------------


@router.post("", response_model=ChatResponse)
async def chat(
    req: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """Non-streaming RAG chat endpoint.

    Returns a complete JSON response with the answer and source attributions.
    The bot must be in READY or READY_WITH_WARNINGS status to accept requests.
    """
    bot = await _get_ready_bot(req.bot_id, db)
    bot_name = await _get_bot_name(req.bot_id, db)

    rag_request = RAGRequest(
        bot_id=req.bot_id,
        session_id=req.session_id,
        user_message=req.message,
        history=[],  # History loaded inside rag.py from DB
        db=db,
        bot_name=bot_name,
    )

    rag_response = await chat_with_rag(rag_request)

    return ChatResponse(
        answer=rag_response.answer,
        sources=[
            SourceRef(url=s["url"], title=s.get("title"))
            for s in rag_response.sources
        ],
    )


# ---------------------------------------------------------------------------
# POST /api/chat/stream — SSE streaming chat
# ---------------------------------------------------------------------------


@router.post("/stream")
async def chat_stream(
    req: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """Streaming RAG chat endpoint using Server-Sent Events (SSE).

    Events emitted (per PRD Section 6.3.4):
        event: token  → data: {"text": "..."}
        event: sources → data: [{"url": "...", "title": "..."}]
        event: done   → data: {"status": "complete"}
        event: error  → data: {"code": "...", "message": "..."}
    """
    bot = await _get_ready_bot(req.bot_id, db)
    bot_name = await _get_bot_name(req.bot_id, db)

    rag_request = RAGRequest(
        bot_id=req.bot_id,
        session_id=req.session_id,
        user_message=req.message,
        history=[],
        db=db,
        bot_name=bot_name,
    )

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            async for event in stream_chat_with_rag(rag_request):
                event_type = event["event"]
                data = event["data"]
                # Format: "event: {type}\ndata: {json}\n\n"
                yield f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
        except Exception as exc:
            logger.error("SSE stream error: %s", exc, exc_info=True)
            yield f"event: error\ndata: {json.dumps({'code': 'STREAM_ERROR', 'message': str(exc)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
