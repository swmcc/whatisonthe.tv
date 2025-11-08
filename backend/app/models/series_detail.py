"""Series detail model."""

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from app.models.content import Content


class SeriesDetail(Base):
    """Series-specific details (one-to-one with Content where content_type='series')."""

    __tablename__ = "series_detail"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Foreign key to content (belongs_to)
    content_id: Mapped[int] = mapped_column(
        ForeignKey("content.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )

    # Series-specific fields
    number_of_seasons: Mapped[int | None] = mapped_column(Integer)
    number_of_episodes: Mapped[int | None] = mapped_column(Integer)
    average_runtime: Mapped[int | None] = mapped_column(Integer)
    first_air_date: Mapped[date | None] = mapped_column(Date)
    last_air_date: Mapped[date | None] = mapped_column(Date)
    network: Mapped[str | None] = mapped_column(String(100))
    production_company: Mapped[str | None] = mapped_column(String(255))

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

    # Relationships - belongs_to
    content: Mapped["Content"] = relationship(
        "Content",
        back_populates="series_detail"
    )

    def __repr__(self) -> str:
        """String representation of SeriesDetail."""
        return f"<SeriesDetail(id={self.id}, content_id={self.content_id})>"
