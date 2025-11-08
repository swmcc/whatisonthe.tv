"""Person model."""

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, Float, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from app.models.credit import Credit
    from app.models.alias import Alias
    from app.models.content import Content


class Person(Base):
    """Person model for actors, directors, writers, producers, and crew."""

    __tablename__ = "person"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # TVDB reference
    tvdb_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False, index=True)

    # Name fields
    first_name: Mapped[str | None] = mapped_column(String(100))
    last_name: Mapped[str | None] = mapped_column(String(100), index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    slug: Mapped[str | None] = mapped_column(String(255), unique=True, index=True)

    # Bio and images
    image_url: Mapped[str | None] = mapped_column(String(500))
    biography: Mapped[str | None] = mapped_column(Text)

    # Personal details
    birth_date: Mapped[date | None] = mapped_column(Date)
    birth_place: Mapped[str | None] = mapped_column(String(255))

    # Popularity
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

    # Relationships - has_many
    credits: Mapped[list["Credit"]] = relationship(
        "Credit",
        back_populates="person",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    # Filtered credit relationships (viewonly for convenience)
    acting_credits: Mapped[list["Credit"]] = relationship(
        "Credit",
        primaryjoin="and_(Person.id==Credit.person_id, Credit.role_type=='actor')",
        order_by="Credit.sort_order",
        viewonly=True,
        lazy="selectin"
    )

    directing_credits: Mapped[list["Credit"]] = relationship(
        "Credit",
        primaryjoin="and_(Person.id==Credit.person_id, Credit.role_type=='director')",
        viewonly=True,
        lazy="selectin"
    )

    writing_credits: Mapped[list["Credit"]] = relationship(
        "Credit",
        primaryjoin="and_(Person.id==Credit.person_id, Credit.role_type=='writer')",
        viewonly=True,
        lazy="selectin"
    )

    producing_credits: Mapped[list["Credit"]] = relationship(
        "Credit",
        primaryjoin="and_(Person.id==Credit.person_id, Credit.role_type.in_(['producer', 'executive_producer']))",
        viewonly=True,
        lazy="selectin"
    )

    # Aliases (polymorphic relationship)
    aliases: Mapped[list["Alias"]] = relationship(
        "Alias",
        primaryjoin="and_(foreign(Alias.entity_id)==Person.id, Alias.entity_type=='person')",
        foreign_keys="[Alias.entity_id]",
        cascade="all, delete-orphan",
        viewonly=True
    )

    # Indexes
    __table_args__ = (
        Index('idx_person_full_name_search', 'full_name'),
        Index('idx_person_popularity', 'popularity_score'),
    )

    def __repr__(self) -> str:
        """String representation of Person."""
        return f"<Person(id={self.id}, name={self.full_name})>"

    @property
    def series(self) -> list["Content"]:
        """Get all series this person worked on."""
        return [
            credit.content
            for credit in self.credits
            if credit.content and credit.content.content_type == "series"
        ]

    @property
    def movies(self) -> list["Content"]:
        """Get all movies this person worked on."""
        return [
            credit.content
            for credit in self.credits
            if credit.content and credit.content.content_type == "movie"
        ]

    @property
    def filmography_count(self) -> dict[str, int]:
        """Get count of series vs movies."""
        return {
            "series": len([c for c in self.credits if c.content and c.content.content_type == "series"]),
            "movies": len([c for c in self.credits if c.content and c.content.content_type == "movie"]),
        }
