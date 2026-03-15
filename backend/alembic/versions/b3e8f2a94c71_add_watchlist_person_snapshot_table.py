"""Add watchlist person snapshot table.

Revision ID: b3e8f2a94c71
Revises: a17729161b5c
Create Date: 2026-03-15

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "b3e8f2a94c71"
down_revision: Union[str, None] = "a17729161b5c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create watchlist_person_snapshot table."""
    op.create_table(
        "watchlist_person_snapshot",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("watchlist_item_id", sa.Integer(), nullable=False),
        sa.Column("content_tvdb_id", sa.Integer(), nullable=False),
        sa.Column("role_type", sa.String(50), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["watchlist_item_id"],
            ["watchlist.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "watchlist_item_id",
            "content_tvdb_id",
            "role_type",
            name="uq_watchlist_snapshot_item_content_role",
        ),
    )

    # Create indexes
    op.create_index(
        "idx_watchlist_person_snapshot_id",
        "watchlist_person_snapshot",
        ["id"],
    )
    op.create_index(
        "idx_watchlist_person_snapshot_item_id",
        "watchlist_person_snapshot",
        ["watchlist_item_id"],
    )
    op.create_index(
        "idx_watchlist_person_snapshot_content_tvdb_id",
        "watchlist_person_snapshot",
        ["content_tvdb_id"],
    )
    op.create_index(
        "idx_watchlist_snapshot_item_lookup",
        "watchlist_person_snapshot",
        ["watchlist_item_id", "content_tvdb_id", "role_type"],
    )


def downgrade() -> None:
    """Drop watchlist_person_snapshot table."""
    op.drop_index(
        "idx_watchlist_snapshot_item_lookup",
        table_name="watchlist_person_snapshot",
    )
    op.drop_index(
        "idx_watchlist_person_snapshot_content_tvdb_id",
        table_name="watchlist_person_snapshot",
    )
    op.drop_index(
        "idx_watchlist_person_snapshot_item_id",
        table_name="watchlist_person_snapshot",
    )
    op.drop_index(
        "idx_watchlist_person_snapshot_id",
        table_name="watchlist_person_snapshot",
    )
    op.drop_table("watchlist_person_snapshot")
