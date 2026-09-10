import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List, TYPE_CHECKING
from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.bot import Bot
    from app.models.crawl_job import CrawlJob
    from app.models.chunk import Chunk


class Page(Base, TimestampMixin):
    __tablename__ = "pages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    bot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("bots.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    crawl_job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("crawl_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    canonical_url: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    title: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    http_status: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    content_type: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    raw_html: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    clean_text: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    structured_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
    )
    content_hash: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
    )
    crawl_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )  # SUCCESS, FAILED, SKIPPED
    render_mode: Mapped[str] = mapped_column(
        String(20),
        default="HTTP",
        nullable=False,
    )  # HTTP, PLAYWRIGHT
    error_code: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    crawled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    bot: Mapped["Bot"] = relationship(
        "Bot",
        back_populates="pages",
    )
    crawl_job: Mapped["CrawlJob"] = relationship(
        "CrawlJob",
        back_populates="pages",
    )
    chunks: Mapped[List["Chunk"]] = relationship(
        "Chunk",
        back_populates="page",
    )

    __table_args__ = (
        UniqueConstraint("bot_id", "url", name="uq_bot_page_url"),
        Index("idx_pages_bot_id", "bot_id"),
    )
