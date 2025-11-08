"""Alias model for alternative names."""

from datetime import datetime

from sqlalchemy import DateTime, Enum as SQLEnum, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Alias(Base):
    """Alias model for alternative names of content or people."""

    __tablename__ = "alias"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # TVDB reference (if available)
    tvdb_alias_id: Mapped[int | None] = mapped_column(Integer, index=True)

    # Polymorphic fields (points to either Content or Person)
    entity_type: Mapped[str] = mapped_column(
        SQLEnum("content", "person", name="alias_entity_type_enum"),
        nullable=False,
        index=True
    )
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    # Alias information
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    language: Mapped[str] = mapped_column(String(10), default="eng")

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

    # Indexes
    __table_args__ = (
        Index("idx_alias_entity", "entity_type", "entity_id"),
        Index("idx_alias_name_search", "name"),
    )

    def __repr__(self) -> str:
        """String representation of Alias."""
        return f"<Alias(id={self.id}, type={self.entity_type}, entity_id={self.entity_id}, name={self.name})>"
