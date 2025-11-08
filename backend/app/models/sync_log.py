"""Sync log model for tracking TVDB synchronization."""

from datetime import datetime

from sqlalchemy import DateTime, Enum as SQLEnum, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class SyncLog(Base):
    """Sync log for tracking TVDB API synchronization attempts."""

    __tablename__ = "sync_log"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # What was synced
    entity_type: Mapped[str] = mapped_column(
        SQLEnum("content", "person", name="sync_entity_type_enum"),
        nullable=False,
        index=True
    )
    entity_id: Mapped[int | None] = mapped_column(Integer, index=True)
    tvdb_id: Mapped[int | None] = mapped_column(Integer, index=True)

    # Sync status
    sync_status: Mapped[str] = mapped_column(
        SQLEnum("success", "failed", "partial", name="sync_status_enum"),
        nullable=False,
        index=True
    )

    # Sync type
    sync_type: Mapped[str] = mapped_column(
        SQLEnum("full", "incremental", "metadata_only", name="sync_type_enum"),
        nullable=False
    )

    # Error details (if failed)
    error_message: Mapped[str | None] = mapped_column(Text)

    # Performance tracking
    duration_ms: Mapped[int | None] = mapped_column(Integer)

    # Timestamp
    synced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True
    )

    # Indexes
    __table_args__ = (
        Index("idx_sync_log_entity", "entity_type", "entity_id"),
        Index("idx_sync_log_status_time", "sync_status", "synced_at"),
    )

    def __repr__(self) -> str:
        """String representation of SyncLog."""
        return f"<SyncLog(id={self.id}, type={self.entity_type}, status={self.sync_status}, synced_at={self.synced_at})>"
