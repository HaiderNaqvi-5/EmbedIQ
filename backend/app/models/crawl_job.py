import uuid
from datetime import UTC, datetime
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

utc_now = lambda: datetime.now(UTC)

if TYPE_CHECKING:
    from app.models.bot import Bot
    from app.models.page import Page
    from app.models.document import Document


class CrawlJob(Base):
    __tablename__ = "crawl_jobs"

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
    status: Mapped[str] = mapped_column(
        String(50),
        default="QUEUED",
        nullable=False,
    )  # QUEUED, RUNNING, COMPLETED, FAILED
    stage: Mapped[str] = mapped_column(
        String(50),
        default="QUEUED",
        nullable=False,
    )  # VALIDATING, DISCOVERING, CRAWLING, EXTRACTING, BRANDING, GENERATING_KNOWLEDGE, CHUNKING, EMBEDDING, INDEXING, COMPLETED
    total_pages: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    processed_pages: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    failed_pages: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    warning_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    error_code: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    # Relationships
    bot: Mapped["Bot"] = relationship(
        "Bot",
        back_populates="crawl_jobs",
    )
    pages: Mapped[List["Page"]] = relationship(
        "Page",
        back_populates="crawl_job",
        cascade="all, delete-orphan",
    )
    documents: Mapped[List["Document"]] = relationship(
        "Document",
        back_populates="crawl_job",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_crawl_jobs_bot_created", "bot_id", "created_at"),
    )
