"""Episode model for TV series episodes."""

from datetime import datetime, date
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text, JSON, DateTime, Date, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from app.models.content import Content
    from app.models.season import Season


class Episode(Base):
    """Episode model for TV series episodes."""

    __tablename__ = "episode"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # TVDB reference
    tvdb_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False, index=True)

    # Foreign keys
    content_id: Mapped[int] = mapped_column(ForeignKey("content.id", ondelete="CASCADE"), nullable=False)
    season_id: Mapped[int | None] = mapped_column(ForeignKey("season.id", ondelete="CASCADE"))

    # Episode details
    season_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    episode_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    absolute_number: Mapped[int | None] = mapped_column(Integer)

    name: Mapped[str | None] = mapped_column(String(500))
    overview: Mapped[str | None] = mapped_column(Text)

    # Images
    image_url: Mapped[str | None] = mapped_column(String(500))

    # Air date and runtime
    aired: Mapped[date | None] = mapped_column(Date)
    runtime: Mapped[int | None] = mapped_column(Integer)  # In minutes
    year: Mapped[str | None] = mapped_column(String(10))

    # Episode type
    is_movie: Mapped[bool | None] = mapped_column(Integer, default=0)  # Special episodes that are movie-length
    finale_type: Mapped[str | None] = mapped_column(String(50))  # season, series, mid-season, etc.

    # Special episode ordering
    airs_before_season: Mapped[int | None] = mapped_column(Integer)
    airs_before_episode: Mapped[int | None] = mapped_column(Integer)
    airs_after_season: Mapped[int | None] = mapped_column(Integer)

    # Metadata
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    extra_metadata: Mapped[dict | None] = mapped_column(JSON)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    content: Mapped["Content"] = relationship("Content", back_populates="episodes")
    season: Mapped["Season | None"] = relationship("Season", back_populates="episodes")

    __table_args__ = (
        Index('idx_episode_content', 'content_id'),
        Index('idx_episode_season', 'season_id'),
        Index('idx_episode_numbers', 'content_id', 'season_number', 'episode_number'),
        Index('idx_episode_tvdb', 'tvdb_id'),
        Index('idx_episode_aired', 'aired'),
    )

    def __repr__(self) -> str:
        """String representation of Episode."""
        return f"<Episode(id={self.id}, S{self.season_number:02d}E{self.episode_number:02d}, name={self.name})>"
