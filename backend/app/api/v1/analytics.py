"""
Authenticated analytics endpoints for the current EmbedIQ workspace.

All statistics are derived from persisted Bot, Conversation and Message rows.
Every query is scoped through Bot.user_id to prevent cross-user analytics access.
"""

import asyncio
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, select

from app.api.deps import get_current_user
from app.db.session import AsyncSessionLocal
from app.models.bot import Bot
from app.models.conversation import Conversation, Message
from app.models.user import User

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("")
async def get_analytics(
    current_user: User = Depends(get_current_user),
):
    """
    Return real workspace analytics for the authenticated user.

    Includes:
    - total conversations
    - total messages
    - user questions
    - assistant responses
    - today's activity
    - average messages per conversation
    - bots with conversations
    - 7-day activity
    - per-bot analytics
    - recent conversations
    """

    user_id = current_user.id

    now = datetime.now(UTC)
    today_start = now.replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )

    seven_days_start = today_start - timedelta(days=6)

    async def _execute_scalar(query):
        async with AsyncSessionLocal() as session:
            result = await session.execute(query)
            return result.scalar_one()

    async def _execute_all(query):
        async with AsyncSessionLocal() as session:
            result = await session.execute(query)
            return result.all()

    # ⚡ Bolt Optimization: Combine scalar counts into a single query to prevent DB connection pool exhaustion.
    # Previously, 8 separate scalar queries executed concurrently consumed 8 distinct connections.
    # Combining them via scalar_subquery().label() executes them in one trip to the DB, saving 7 connections per request.
    q_combined_scalars = select(
        select(func.count(Bot.id)).where(Bot.user_id == user_id).scalar_subquery().label("total_bots"),

        select(func.count(Conversation.id))
        .join(Bot, Conversation.bot_id == Bot.id)
        .where(Bot.user_id == user_id).scalar_subquery().label("total_conversations"),

        select(func.count(Message.id))
        .join(Conversation, Message.conversation_id == Conversation.id)
        .join(Bot, Conversation.bot_id == Bot.id)
        .where(Bot.user_id == user_id).scalar_subquery().label("total_messages"),

        select(func.count(Message.id))
        .join(Conversation, Message.conversation_id == Conversation.id)
        .join(Bot, Conversation.bot_id == Bot.id)
        .where(Bot.user_id == user_id, Message.role == "user").scalar_subquery().label("user_questions"),

        select(func.count(Message.id))
        .join(Conversation, Message.conversation_id == Conversation.id)
        .join(Bot, Conversation.bot_id == Bot.id)
        .where(Bot.user_id == user_id, Message.role == "assistant").scalar_subquery().label("assistant_responses"),

        select(func.count(Conversation.id))
        .join(Bot, Conversation.bot_id == Bot.id)
        .where(Bot.user_id == user_id, Conversation.created_at >= today_start).scalar_subquery().label("conversations_today"),

        select(func.count(Message.id))
        .join(Conversation, Message.conversation_id == Conversation.id)
        .join(Bot, Conversation.bot_id == Bot.id)
        .where(Bot.user_id == user_id, Message.created_at >= today_start).scalar_subquery().label("messages_today"),

        select(func.count(func.distinct(Conversation.bot_id)))
        .join(Bot, Conversation.bot_id == Bot.id)
        .where(Bot.user_id == user_id).scalar_subquery().label("active_bots")
    )

    q_conversation_activity = (
        select(
            func.date(Conversation.created_at).label("day"),
            func.count(Conversation.id).label("count"),
        )
        .join(Bot, Conversation.bot_id == Bot.id)
        .where(
            Bot.user_id == user_id,
            Conversation.created_at >= seven_days_start,
        )
        .group_by(func.date(Conversation.created_at))
    )

    q_message_activity = (
        select(
            func.date(Message.created_at).label("day"),
            func.count(Message.id).label("count"),
        )
        .join(
            Conversation,
            Message.conversation_id == Conversation.id,
        )
        .join(Bot, Conversation.bot_id == Bot.id)
        .where(
            Bot.user_id == user_id,
            Message.created_at >= seven_days_start,
        )
        .group_by(func.date(Message.created_at))
    )

    conversation_count = (
        select(func.count(Conversation.id))
        .where(Conversation.bot_id == Bot.id)
        .correlate(Bot)
        .scalar_subquery()
    )

    message_count = (
        select(func.count(Message.id))
        .join(
            Conversation,
            Message.conversation_id == Conversation.id,
        )
        .where(Conversation.bot_id == Bot.id)
        .correlate(Bot)
        .scalar_subquery()
    )

    last_activity = (
        select(func.max(Message.created_at))
        .join(
            Conversation,
            Message.conversation_id == Conversation.id,
        )
        .where(Conversation.bot_id == Bot.id)
        .correlate(Bot)
        .scalar_subquery()
    )

    q_bot_rows = (
        select(
            Bot.id,
            Bot.name,
            Bot.website_url,
            Bot.status,
            conversation_count.label("conversation_count"),
            message_count.label("message_count"),
            last_activity.label("last_activity"),
        )
        .where(Bot.user_id == user_id)
        .order_by(Bot.created_at.desc())
    )

    q_recent_rows = (
        select(
            Conversation.id,
            Conversation.bot_id,
            Conversation.session_id,
            Conversation.created_at,
            Bot.name.label("bot_name"),
            func.count(Message.id).label("message_count"),
            func.max(Message.created_at).label("last_activity"),
        )
        .join(Bot, Conversation.bot_id == Bot.id)
        .outerjoin(
            Message,
            Message.conversation_id == Conversation.id,
        )
        .where(Bot.user_id == user_id)
        .group_by(
            Conversation.id,
            Conversation.bot_id,
            Conversation.session_id,
            Conversation.created_at,
            Bot.name,
        )
        .order_by(Conversation.created_at.desc())
        .limit(10)
    )

    async def _execute_combined_scalars(query):
        async with AsyncSessionLocal() as session:
            result = await session.execute(query)
            return result.one()

    # Execute all queries concurrently
    (
        scalars_result,
        conversation_activity_result,
        message_activity_result,
        bot_rows,
        recent_rows,
    ) = await asyncio.gather(
        _execute_combined_scalars(q_combined_scalars),
        _execute_all(q_conversation_activity),
        _execute_all(q_message_activity),
        _execute_all(q_bot_rows),
        _execute_all(q_recent_rows),
    )

    # --------------------------------------------------------
    # Process results
    # --------------------------------------------------------

    total_bots = scalars_result.total_bots
    total_conversations = scalars_result.total_conversations
    total_messages = scalars_result.total_messages
    user_questions = scalars_result.user_questions
    assistant_responses = scalars_result.assistant_responses
    conversations_today = scalars_result.conversations_today
    messages_today = scalars_result.messages_today
    active_bots = scalars_result.active_bots

    average_messages_per_conversation = (
        round(total_messages / total_conversations, 2)
        if total_conversations
        else 0
    )

    conversation_activity = {
        str(row.day): row.count
        for row in conversation_activity_result
    }

    message_activity = {
        str(row.day): row.count
        for row in message_activity_result
    }

    activity = []

    for offset in range(7):
        day = (seven_days_start + timedelta(days=offset)).date()
        key = str(day)

        activity.append(
            {
                "date": key,
                "conversations": conversation_activity.get(key, 0),
                "messages": message_activity.get(key, 0),
            }
        )

    bots = [
        {
            "bot_id": str(row.id),
            "bot_name": row.name,
            "website_url": row.website_url,
            "status": row.status,
            "conversations": row.conversation_count or 0,
            "messages": row.message_count or 0,
            "last_activity": (
                row.last_activity.isoformat()
                if row.last_activity
                else None
            ),
        }
        for row in bot_rows
    ]

    recent_conversations = [
        {
            "conversation_id": str(row.id),
            "bot_id": str(row.bot_id),
            "bot_name": row.bot_name,
            "session_id": row.session_id,
            "created_at": row.created_at.isoformat(),
            "last_activity": (
                row.last_activity.isoformat()
                if row.last_activity
                else None
            ),
            "message_count": row.message_count,
        }
        for row in recent_rows
    ]

    return {
        "summary": {
            "total_bots": total_bots,
            "active_bots": active_bots,
            "total_conversations": total_conversations,
            "total_messages": total_messages,
            "user_questions": user_questions,
            "assistant_responses": assistant_responses,
            "conversations_today": conversations_today,
            "messages_today": messages_today,
            "average_messages_per_conversation": average_messages_per_conversation,
        },
        "activity": activity,
        "bots": bots,
        "recent_conversations": recent_conversations,
    }
