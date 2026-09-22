import uuid
from datetime import UTC, datetime
from typing import Optional, Dict, Any, List, TYPE_CHECKING
from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from app.db.base import Base

utc_now = lambda: datetime.now(UTC)

if TYPE_CHECKING:
    from app.models.bot import Bot
    from app.models.document import Document
    from app.models.page import Page


class Chunk(Base):
    __tablename__ = "chunks"

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
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    page_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pages.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    source_url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    page_title: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    heading_path: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    content_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )
    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    token_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    embedding = mapped_column(
        Vector(1536),
        nullable=True,
    )
    metadata_: Mapped[Dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        default=dict,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    # Relationships
    bot: Mapped["Bot"] = relationship(
        "Bot",
        back_populates="chunks",
    )
    document: Mapped["Document"] = relationship(
        "Document",
        back_populates="chunks",
    )
    page: Mapped[Optional["Page"]] = relationship(
        "Page",
        back_populates="chunks",
    )

    __table_args__ = (
        Index("idx_chunks_bot_id", "bot_id"),
        Index("idx_chunks_doc_id", "document_id"),
        Index(
            "idx_chunks_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )
