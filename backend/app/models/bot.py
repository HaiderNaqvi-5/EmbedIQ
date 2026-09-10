import uuid
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.crawl_job import CrawlJob
    from app.models.page import Page
    from app.models.document import Document
    from app.models.chunk import Chunk
    from app.models.brand import BrandSettings
    from app.models.conversation import Conversation


class Bot(Base, TimestampMixin):
    __tablename__ = "bots"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    website_url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    normalized_origin: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default="PENDING",
        nullable=False,
    )  # PENDING, CRAWLING, PROCESSING, INDEXING, READY, READY_WITH_WARNINGS, FAILED
    last_error: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="bots",
    )
    crawl_jobs: Mapped[List["CrawlJob"]] = relationship(
        "CrawlJob",
        back_populates="bot",
        cascade="all, delete-orphan",
    )
    pages: Mapped[List["Page"]] = relationship(
        "Page",
        back_populates="bot",
        cascade="all, delete-orphan",
    )
    documents: Mapped[List["Document"]] = relationship(
        "Document",
        back_populates="bot",
        cascade="all, delete-orphan",
    )
    chunks: Mapped[List["Chunk"]] = relationship(
        "Chunk",
        back_populates="bot",
        cascade="all, delete-orphan",
    )
    brand_settings: Mapped[Optional["BrandSettings"]] = relationship(
        "BrandSettings",
        back_populates="bot",
        uselist=False,
        cascade="all, delete-orphan",
    )
    conversations: Mapped[List["Conversation"]] = relationship(
        "Conversation",
        back_populates="bot",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_bots_user_id", "user_id"),
        Index("idx_bots_origin", "normalized_origin"),
    )
