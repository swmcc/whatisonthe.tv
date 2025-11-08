"""Movie detail model."""

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from app.models.content import Content


class MovieDetail(Base):
    """Movie-specific details (one-to-one with Content where content_type='movie')."""

    __tablename__ = "movie_detail"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Foreign key to content (belongs_to)
    content_id: Mapped[int] = mapped_column(
        ForeignKey("content.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )

    # Movie-specific fields
    runtime: Mapped[int | None] = mapped_column(Integer)
    release_date: Mapped[date | None] = mapped_column(Date)
    budget: Mapped[int | None] = mapped_column(BigInteger)
    revenue: Mapped[int | None] = mapped_column(BigInteger)
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
        back_populates="movie_detail"
    )

    def __repr__(self) -> str:
        """String representation of MovieDetail."""
        return f"<MovieDetail(id={self.id}, content_id={self.content_id})>"
