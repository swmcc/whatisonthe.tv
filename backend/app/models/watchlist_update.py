"""Watchlist update model for tracking status changes."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.watchlist import WatchlistItem


class UpdateType(str, Enum):
    """Type of watchlist update."""

    STATUS_CHANGE = "status_change"
    NEW_EPISODE = "new_episode"
    NEW_CAST = "new_cast"
    METADATA_UPDATE = "metadata_update"


class WatchlistUpdate(Base):
    """Watchlist update model for notifying users of changes."""

    __tablename__ = "watchlist_update"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # User who owns the watchlist item
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Watchlist item this update is for
    watchlist_item_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("watchlist.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Type of update
    update_type: Mapped[UpdateType] = mapped_column(
        SQLEnum(
            UpdateType,
            name="update_type_enum",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        index=True,
    )

    # Human-readable description of the update
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Additional details (e.g., old/new status, episode info)
    details: Mapped[dict | None] = mapped_column(JSONB)

    # Read status
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="watchlist_updates")
    watchlist_item: Mapped["WatchlistItem"] = relationship(
        "WatchlistItem", back_populates="updates", lazy="selectin"
    )

    # Indexes
    __table_args__ = (
        Index("idx_watchlist_update_user_unread", "user_id", "is_read"),
        Index("idx_watchlist_update_created", "created_at"),
    )

    def __repr__(self) -> str:
        """String representation of WatchlistUpdate."""
        return f"<WatchlistUpdate(id={self.id}, user_id={self.user_id}, type={self.update_type})>"
