"""WatchlistContentSnapshot model for tracking known cast when content is added to watchlist."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from app.models.watchlist import WatchlistItem


class WatchlistContentSnapshot(Base):
    """
    Stores the known cast (person TVDB IDs) for content at the time it was added to the watchlist.

    This is used to detect new cast members - any person found via TVDB API that is NOT in this
    snapshot is considered a new cast member and will generate an update notification.
    """

    __tablename__ = "watchlist_content_snapshot"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Foreign key to the watchlist item
    watchlist_item_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("watchlist.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # The TVDB ID of the person in the cast
    person_tvdb_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    # The role type (actor, director, etc.) - for filtering
    role_type: Mapped[str] = mapped_column(String(50), nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    watchlist_item: Mapped["WatchlistItem"] = relationship(
        "WatchlistItem",
        back_populates="content_snapshot_cast",
    )

    # Constraints and indexes
    __table_args__ = (
        # Unique constraint: same person/role can only appear once per watchlist item
        UniqueConstraint(
            "watchlist_item_id",
            "person_tvdb_id",
            "role_type",
            name="uq_watchlist_content_snapshot_item_person_role",
        ),
        # Index for efficient lookup
        Index(
            "idx_watchlist_content_snapshot_item_lookup",
            "watchlist_item_id",
            "person_tvdb_id",
            "role_type",
        ),
    )

    def __repr__(self) -> str:
        """String representation of WatchlistContentSnapshot."""
        return (
            f"<WatchlistContentSnapshot(id={self.id}, "
            f"watchlist_item_id={self.watchlist_item_id}, "
            f"person_tvdb_id={self.person_tvdb_id}, "
            f"role_type={self.role_type})>"
        )
