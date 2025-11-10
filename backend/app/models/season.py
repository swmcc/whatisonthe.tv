"""Season model for TV series seasons."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text, JSON, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from app.models.content import Content
    from app.models.episode import Episode


class Season(Base):
    """Season model for TV series."""

    __tablename__ = "season"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # TVDB reference
    tvdb_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False, index=True)

    # Foreign key to content (series)
    content_id: Mapped[int] = mapped_column(ForeignKey("content.id", ondelete="CASCADE"), nullable=False)

    # Season details
    season_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    name: Mapped[str | None] = mapped_column(String(255))
    overview: Mapped[str | None] = mapped_column(Text)

    # Images
    image_url: Mapped[str | None] = mapped_column(String(500))

    # Season type (Aired Order, DVD Order, etc.)
    season_type: Mapped[str | None] = mapped_column(String(100))
    season_type_id: Mapped[int | None] = mapped_column(Integer)

    # Air dates
    year: Mapped[str | None] = mapped_column(String(10))

    # Metadata
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    extra_metadata: Mapped[dict | None] = mapped_column(JSON)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    content: Mapped["Content"] = relationship("Content", back_populates="seasons")
    episodes: Mapped[list["Episode"]] = relationship(
        "Episode", back_populates="season", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index('idx_season_content', 'content_id'),
        Index('idx_season_number', 'content_id', 'season_number'),
        Index('idx_season_tvdb', 'tvdb_id'),
    )

    def __repr__(self) -> str:
        """String representation of Season."""
        return f"<Season(id={self.id}, content_id={self.content_id}, season={self.season_number})>"
