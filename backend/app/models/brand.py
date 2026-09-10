import uuid
from datetime import datetime
from typing import Optional, Dict, Any, TYPE_CHECKING
from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.bot import Bot


class BrandSettings(Base):
    __tablename__ = "brand_settings"

    bot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("bots.id", ondelete="CASCADE"),
        primary_key=True,
    )
    company_name: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    tagline: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    logo_url: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    favicon_url: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    primary_color: Mapped[str] = mapped_column(
        String(30),
        default="#2563EB",
        nullable=False,
    )
    secondary_color: Mapped[str] = mapped_column(
        String(30),
        default="#1E40AF",
        nullable=False,
    )
    background_color: Mapped[str] = mapped_column(
        String(30),
        default="#FFFFFF",
        nullable=False,
    )
    text_color: Mapped[str] = mapped_column(
        String(30),
        default="#111827",
        nullable=False,
    )
    accent_color: Mapped[str] = mapped_column(
        String(30),
        default="#3B82F6",
        nullable=False,
    )
    font_family: Mapped[str] = mapped_column(
        Text,
        default="Inter, sans-serif",
        nullable=False,
    )
    theme: Mapped[str] = mapped_column(
        String(20),
        default="light",
        nullable=False,
    )
    border_radius: Mapped[str] = mapped_column(
        String(20),
        default="12px",
        nullable=False,
    )
    widget_position: Mapped[str] = mapped_column(
        String(20),
        default="bottom-right",
        nullable=False,
    )
    confidence: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    bot: Mapped["Bot"] = relationship(
        "Bot",
        back_populates="brand_settings",
    )
