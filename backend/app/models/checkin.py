"""Checkin model."""

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class FocusLevel(str, enum.Enum):
    """Focus level during viewing."""

    FOCUSED = "focused"
    DISTRACTED = "distracted"
    BACKGROUND = "background"
    SLEEP = "sleep"


class Checkin(Base):
    """Checkin model for tracking when users watch movies or TV episodes."""

    __tablename__ = "checkins"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    content_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("content.id", ondelete="CASCADE"), nullable=False, index=True
    )
    episode_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("episode.id", ondelete="CASCADE"), nullable=True, index=True
    )
    watched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    watched_with: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    focus: Mapped[Optional[FocusLevel]] = mapped_column(
        Enum(FocusLevel, name="focuslevel", create_type=False), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="checkins")
    content: Mapped["Content"] = relationship("Content", back_populates="checkins")
    episode: Mapped[Optional["Episode"]] = relationship("Episode", back_populates="checkins")

    def __repr__(self) -> str:
        """String representation of Checkin."""
        episode_str = f", episode_id={self.episode_id}" if self.episode_id else ""
        return f"<Checkin(id={self.id}, user_id={self.user_id}, content_id={self.content_id}{episode_str}, watched_at={self.watched_at})>"
