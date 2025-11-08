"""Credit model (junction table between Content and Person)."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from app.models.content import Content
    from app.models.person import Person


class Credit(Base):
    """Credit model linking content to people with their roles."""

    __tablename__ = "credit"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # TVDB reference (if available)
    tvdb_credit_id: Mapped[int | None] = mapped_column(Integer, index=True)

    # Foreign keys (belongs_to)
    content_id: Mapped[int] = mapped_column(
        ForeignKey("content.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    person_id: Mapped[int] = mapped_column(
        ForeignKey("person.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Role information
    role_type: Mapped[str] = mapped_column(
        SQLEnum(
            "actor",
            "director",
            "writer",
            "producer",
            "executive_producer",
            "cinematographer",
            "composer",
            "editor",
            "crew",
            name="role_type_enum"
        ),
        nullable=False,
        index=True
    )

    # Additional role details
    character_name: Mapped[str | None] = mapped_column(String(255))  # For actors
    department: Mapped[str | None] = mapped_column(String(100))  # For crew
    job_title: Mapped[str | None] = mapped_column(String(100))  # Specific role

    # Billing order
    sort_order: Mapped[int] = mapped_column(Integer, default=999)

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
        back_populates="credits"
    )
    person: Mapped["Person"] = relationship(
        "Person",
        back_populates="credits"
    )

    # Constraints and indexes
    __table_args__ = (
        # Unique constraint: same person can't have same role/character on same content
        UniqueConstraint(
            "content_id",
            "person_id",
            "role_type",
            "character_name",
            name="uq_content_person_role_character"
        ),
        # Index for ordering by billing
        Index("idx_credit_content_sort", "content_id", "sort_order"),
        # Index for reverse lookup (person to content)
        Index("idx_credit_person_content", "person_id", "content_id"),
    )

    def __repr__(self) -> str:
        """String representation of Credit."""
        return f"<Credit(id={self.id}, person_id={self.person_id}, content_id={self.content_id}, role={self.role_type})>"

    @property
    def is_actor(self) -> bool:
        """Check if credit is for an actor role."""
        return self.role_type == "actor"

    @property
    def is_director(self) -> bool:
        """Check if credit is for a director role."""
        return self.role_type == "director"

    @property
    def is_writer(self) -> bool:
        """Check if credit is for a writer role."""
        return self.role_type == "writer"

    @property
    def is_producer(self) -> bool:
        """Check if credit is for a producer role."""
        return self.role_type in ["producer", "executive_producer"]
