import uuid
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class BrandSettingsResponse(BaseModel):
    bot_id: uuid.UUID
    company_name: Optional[str] = None
    tagline: Optional[str] = None
    logo_url: Optional[str] = None
    favicon_url: Optional[str] = None
    primary_color: str = "#2563EB"
    secondary_color: str = "#1E40AF"
    background_color: str = "#FFFFFF"
    text_color: str = "#111827"
    accent_color: str = "#3B82F6"
    font_family: str = "Inter, sans-serif"
    theme: str = "light"
    border_radius: str = "12px"
    widget_position: str = "bottom-right"
    confidence: Dict[str, Any] = Field(default_factory=dict)
    updated_at: datetime

    class Config:
        from_attributes = True


class BrandSettingsUpdateRequest(BaseModel):
    company_name: Optional[str] = None
    tagline: Optional[str] = None
    logo_url: Optional[str] = None
    favicon_url: Optional[str] = None
    primary_color: Optional[str] = Field(None, pattern=r"^#(?:[0-9a-fA-F]{3}){1,2}$")
    secondary_color: Optional[str] = Field(None, pattern=r"^#(?:[0-9a-fA-F]{3}){1,2}$")
    background_color: Optional[str] = Field(None, pattern=r"^#(?:[0-9a-fA-F]{3}){1,2}$")
    text_color: Optional[str] = Field(None, pattern=r"^#(?:[0-9a-fA-F]{3}){1,2}$")
    accent_color: Optional[str] = Field(None, pattern=r"^#(?:[0-9a-fA-F]{3}){1,2}$")
    font_family: Optional[str] = None
    theme: Optional[str] = Field(None, pattern=r"^(light|dark)$")
    border_radius: Optional[str] = None
    widget_position: Optional[str] = Field(None, pattern=r"^(bottom-right|bottom-left|top-right|top-left)$")
