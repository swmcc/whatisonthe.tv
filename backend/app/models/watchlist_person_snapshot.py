"""WatchlistPersonSnapshot model for tracking known credits when a person is added to watchlist."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from app.models.watchlist import WatchlistItem


class WatchlistPersonSnapshot(Base):
    """
    Stores the known credits (TVDB IDs) for a person at the time they were added to the watchlist.

    This is used to detect new credits - any credit found via TVDB API that is NOT in this
    snapshot is considered a new credit and will generate an update notification.
    """

    __tablename__ = "watchlist_person_snapshot"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Foreign key to the watchlist item
    watchlist_item_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("watchlist.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # The TVDB ID of the content (series or movie) the person is credited in
    content_tvdb_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    # The role type for this credit (actor, director, etc.)
    role_type: Mapped[str] = mapped_column(String(50), nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    # Relationships
    watchlist_item: Mapped["WatchlistItem"] = relationship(
        "WatchlistItem",
        back_populates="person_snapshot_credits",
    )

    # Constraints and indexes
    __table_args__ = (
        # Unique constraint: same content/role can only appear once per watchlist item
        UniqueConstraint(
            "watchlist_item_id",
            "content_tvdb_id",
            "role_type",
            name="uq_watchlist_snapshot_item_content_role",
        ),
        # Index for efficient lookup
        Index(
            "idx_watchlist_snapshot_item_lookup",
            "watchlist_item_id",
            "content_tvdb_id",
            "role_type",
        ),
    )

    def __repr__(self) -> str:
        """String representation of WatchlistPersonSnapshot."""
        return (
            f"<WatchlistPersonSnapshot(id={self.id}, "
            f"watchlist_item_id={self.watchlist_item_id}, "
            f"content_tvdb_id={self.content_tvdb_id}, "
            f"role_type={self.role_type})>"
        )
