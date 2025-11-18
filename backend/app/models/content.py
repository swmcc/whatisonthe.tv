"""Content models (series and movies)."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, Integer, String, Text, Enum as SQLEnum, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from app.models.credit import Credit
    from app.models.genre import Genre
    from app.models.series_detail import SeriesDetail
    from app.models.movie_detail import MovieDetail
    from app.models.alias import Alias
    from app.models.season import Season
    from app.models.episode import Episode
    from app.models.checkin import Checkin


class Content(Base):
    """Base content model for both series and movies."""

    __tablename__ = "content"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # TVDB reference
    tvdb_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False, index=True)

    # Content type
    content_type: Mapped[str] = mapped_column(
        SQLEnum("series", "movie", name="content_type_enum"),
        nullable=False,
        index=True
    )

    # Basic information
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    slug: Mapped[str | None] = mapped_column(String(255), unique=True, index=True)
    overview: Mapped[str | None] = mapped_column(Text)
    year: Mapped[int | None] = mapped_column(Integer, index=True)
    status: Mapped[str | None] = mapped_column(String(50))

    # Images
    image_url: Mapped[str | None] = mapped_column(String(500))
    poster_url: Mapped[str | None] = mapped_column(String(500))
    backdrop_url: Mapped[str | None] = mapped_column(String(500))

    # Metadata
    original_language: Mapped[str | None] = mapped_column(String(10))
    original_country: Mapped[str | None] = mapped_column(String(10))
    popularity_score: Mapped[float] = mapped_column(Float, default=0.0)

    # TVDB sync tracking
    tvdb_last_updated: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)

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

    # Extra TVDB data
    extra_metadata: Mapped[dict | None] = mapped_column(JSONB)

    # Relationships - has_one (uselist=False means one-to-one)
    series_detail: Mapped["SeriesDetail | None"] = relationship(
        "SeriesDetail",
        back_populates="content",
        uselist=False,
        cascade="all, delete-orphan"
    )
    movie_detail: Mapped["MovieDetail | None"] = relationship(
        "MovieDetail",
        back_populates="content",
        uselist=False,
        cascade="all, delete-orphan"
    )

    # Relationships - has_many
    credits: Mapped[list["Credit"]] = relationship(
        "Credit",
        back_populates="content",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    # Filtered credit relationships (viewonly for convenience)
    actors: Mapped[list["Credit"]] = relationship(
        "Credit",
        primaryjoin="and_(Content.id==Credit.content_id, Credit.role_type=='actor')",
        order_by="Credit.sort_order",
        viewonly=True,
        lazy="selectin"
    )

    directors: Mapped[list["Credit"]] = relationship(
        "Credit",
        primaryjoin="and_(Content.id==Credit.content_id, Credit.role_type=='director')",
        viewonly=True,
        lazy="selectin"
    )

    writers: Mapped[list["Credit"]] = relationship(
        "Credit",
        primaryjoin="and_(Content.id==Credit.content_id, Credit.role_type=='writer')",
        viewonly=True,
        lazy="selectin"
    )

    producers: Mapped[list["Credit"]] = relationship(
        "Credit",
        primaryjoin="and_(Content.id==Credit.content_id, Credit.role_type.in_(['producer', 'executive_producer']))",
        viewonly=True,
        lazy="selectin"
    )

    # Many-to-many with Genre
    genres: Mapped[list["Genre"]] = relationship(
        "Genre",
        secondary="content_genre",
        back_populates="content",
        lazy="selectin"
    )

    # Aliases (polymorphic relationship)
    aliases: Mapped[list["Alias"]] = relationship(
        "Alias",
        primaryjoin="and_(foreign(Alias.entity_id)==Content.id, Alias.entity_type=='content')",
        foreign_keys="[Alias.entity_id]",
        cascade="all, delete-orphan",
        viewonly=True
    )

    # Seasons (for series only)
    seasons: Mapped[list["Season"]] = relationship(
        "Season",
        back_populates="content",
        cascade="all, delete-orphan",
        order_by="Season.season_number"
    )

    # Episodes (for series only)
    episodes: Mapped[list["Episode"]] = relationship(
        "Episode",
        back_populates="content",
        cascade="all, delete-orphan",
        order_by="(Episode.season_number, Episode.episode_number)"
    )

    # Checkins
    checkins: Mapped[list["Checkin"]] = relationship(
        "Checkin",
        back_populates="content",
        cascade="all, delete-orphan",
        order_by="Checkin.watched_at.desc()"
    )

    # Indexes
    __table_args__ = (
        Index('idx_content_popularity', 'popularity_score'),
        Index('idx_content_name_search', 'name'),
    )

    def __repr__(self) -> str:
        """String representation of Content."""
        return f"<Content(id={self.id}, type={self.content_type}, name={self.name})>"

    @property
    def is_series(self) -> bool:
        """Check if content is a series."""
        return self.content_type == "series"

    @property
    def is_movie(self) -> bool:
        """Check if content is a movie."""
        return self.content_type == "movie"
