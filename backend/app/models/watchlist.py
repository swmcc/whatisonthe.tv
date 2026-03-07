"""Watchlist model."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Text, UniqueConstraint
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from app.models.content import Content
    from app.models.person import Person
    from app.models.user import User


class WatchlistItemType(str, Enum):
    """Type of watchlist item."""

    CONTENT = "content"
    PERSON = "person"


class PersonRoleFilter(str, Enum):
    """Filter for person roles to watch for."""

    ANY = "any"
    ACTOR = "actor"
    DIRECTOR = "director"


class WatchlistItem(Base):
    """Watchlist item model for tracking shows, movies, and people to follow."""

    __tablename__ = "watchlist"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # User who owns the item
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Item type (content or person)
    item_type: Mapped[WatchlistItemType] = mapped_column(
        SQLEnum(
            WatchlistItemType,
            name="watchlist_item_type_enum",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        index=True,
    )

    # Content reference (for shows/movies)
    content_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("content.id", ondelete="CASCADE"), nullable=True, index=True
    )

    # Person reference (for actors/directors)
    person_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("person.id", ondelete="CASCADE"), nullable=True, index=True
    )

    # Role filter for persons (what role to watch for)
    person_role_filter: Mapped[PersonRoleFilter | None] = mapped_column(
        SQLEnum(
            PersonRoleFilter,
            name="person_role_filter_enum",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=True,
        default=PersonRoleFilter.ANY,
    )

    # Optional notes
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="watchlist_items")
    content: Mapped["Content | None"] = relationship("Content", lazy="selectin")
    person: Mapped["Person | None"] = relationship("Person", lazy="selectin")

    # Indexes and constraints
    __table_args__ = (
        # Unique constraint: user can only have one watchlist entry per content
        UniqueConstraint("user_id", "content_id", name="uq_watchlist_user_content"),
        # Unique constraint: user can only have one watchlist entry per person
        UniqueConstraint("user_id", "person_id", name="uq_watchlist_user_person"),
        # Index for efficient lookups
        Index("idx_watchlist_user_item_type", "user_id", "item_type"),
    )

    def __repr__(self) -> str:
        """String representation of WatchlistItem."""
        if self.item_type == WatchlistItemType.CONTENT:
            return f"<WatchlistItem(id={self.id}, user_id={self.user_id}, content_id={self.content_id})>"
        return f"<WatchlistItem(id={self.id}, user_id={self.user_id}, person_id={self.person_id})>"
