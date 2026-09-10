"""Pydantic schemas for public Widget endpoints (PRD Section 8.3)."""

import uuid
from typing import Optional
from pydantic import BaseModel


class WidgetTheme(BaseModel):
    """Visual theme configuration served to the widget loader."""

    primary_color: str = "#2563EB"
    secondary_color: str = "#1E40AF"
    background_color: str = "#FFFFFF"
    text_color: str = "#111827"
    accent_color: str = "#3B82F6"
    font_family: str = "Inter, sans-serif"
    border_radius: str = "12px"
    position: str = "bottom-right"


class WidgetConfigResponse(BaseModel):
    """Response for GET /api/widget/config/{bot_id}."""

    bot_id: uuid.UUID
    company_name: Optional[str] = None
    logo_url: Optional[str] = None
    status: str
    theme: WidgetTheme
