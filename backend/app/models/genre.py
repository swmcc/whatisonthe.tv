"""Genre model."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Integer, String, Table, Column, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from app.models.content import Content


# Association table for many-to-many relationship between Content and Genre
content_genre = Table(
    "content_genre",
    Base.metadata,
    Column("content_id", ForeignKey("content.id", ondelete="CASCADE"), primary_key=True),
    Column("genre_id", ForeignKey("genre.id", ondelete="CASCADE"), primary_key=True),
    Column("created_at", DateTime(timezone=True), default=datetime.utcnow, nullable=False),
)


class Genre(Base):
    """Genre model for categorizing content."""

    __tablename__ = "genre"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # TVDB reference
    tvdb_id: Mapped[int | None] = mapped_column(Integer, unique=True, index=True)

    # Genre information
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    slug: Mapped[str | None] = mapped_column(String(100), unique=True, index=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships - has_many through content_genre
    content: Mapped[list["Content"]] = relationship(
        "Content",
        secondary=content_genre,
        back_populates="genres",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        """String representation of Genre."""
        return f"<Genre(id={self.id}, name={self.name})>"
