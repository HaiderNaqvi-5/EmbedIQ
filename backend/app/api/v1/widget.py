"""
Public Widget Configuration Endpoint (PRD Section 8.3)
======================================================
GET /api/widget/config/{bot_id}

Public, unauthenticated endpoint. Returns bot branding/theme configuration
for the widget.js loader. CORS allows all origins (*) so external websites
can fetch this from their end users' browsers.
"""

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.bot import Bot
from app.models.brand import BrandSettings
from app.schemas.widget import WidgetConfigResponse, WidgetTheme

logger = logging.getLogger("embediq.widget")

# Widget endpoints must allow cross-origin requests from any host
router = APIRouter(prefix="/widget", tags=["Widget"])


@router.get("/config/{bot_id}", response_model=WidgetConfigResponse)
async def get_widget_config(
    bot_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Return public bot configuration for the widget.js loader.

    This endpoint is:
      - Unauthenticated (no JWT required).
      - CORS-allowed for all origins (configured at application level).
      - Safe to call from end-user browsers on external websites.

    Only public-safe metadata is returned — no internal credentials,
    user data, or raw knowledge base content.
    """
    # Verify bot exists
    result = await db.execute(
        select(Bot).options(selectinload(Bot.brand_settings)).where(Bot.id == bot_id)
    )
    bot = result.scalar_one_or_none()
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "BOT_NOT_FOUND", "message": "Bot not found"},
        )

    # Load brand settings (may not exist if bot not yet crawled)
    brand = bot.brand_settings

    theme = WidgetTheme(
        primary_color=brand.primary_color if brand else "#2563EB",
        secondary_color=brand.secondary_color if brand else "#1E40AF",
        background_color=brand.background_color if brand else "#FFFFFF",
        text_color=brand.text_color if brand else "#111827",
        accent_color=brand.accent_color if brand else "#3B82F6",
        font_family=brand.font_family if brand else "Inter, sans-serif",
        border_radius=brand.border_radius if brand else "12px",
        position=brand.widget_position if brand else "bottom-right",
    )

    return WidgetConfigResponse(
        bot_id=bot.id,
        company_name=brand.company_name if brand else None,
        logo_url=brand.logo_url if brand else None,
        status=bot.status,
        theme=theme,
    )
