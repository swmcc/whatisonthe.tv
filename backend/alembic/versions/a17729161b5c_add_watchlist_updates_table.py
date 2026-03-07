"""Add watchlist updates table.

Revision ID: a17729161b5c
Revises: c8d2f3a91b47
Create Date: 2026-03-07

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "a17729161b5c"
down_revision: Union[str, None] = "c8d2f3a91b47"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create watchlist_update table."""
    # Create enum type for update_type
    update_type_enum = postgresql.ENUM(
        "status_change",
        "new_episode",
        "new_cast",
        "metadata_update",
        name="update_type_enum",
        create_type=False,
    )
    update_type_enum.create(op.get_bind(), checkfirst=True)

    # Create watchlist_update table
    op.create_table(
        "watchlist_update",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("watchlist_item_id", sa.Integer(), nullable=False),
        sa.Column(
            "update_type",
            postgresql.ENUM(
                "status_change",
                "new_episode",
                "new_cast",
                "metadata_update",
                name="update_type_enum",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("details", postgresql.JSONB(), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["watchlist_item_id"],
            ["watchlist.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes
    op.create_index("idx_watchlist_update_id", "watchlist_update", ["id"])
    op.create_index("idx_watchlist_update_user_id", "watchlist_update", ["user_id"])
    op.create_index(
        "idx_watchlist_update_watchlist_item_id",
        "watchlist_update",
        ["watchlist_item_id"],
    )
    op.create_index(
        "idx_watchlist_update_update_type", "watchlist_update", ["update_type"]
    )
    op.create_index("idx_watchlist_update_is_read", "watchlist_update", ["is_read"])
    op.create_index(
        "idx_watchlist_update_user_unread",
        "watchlist_update",
        ["user_id", "is_read"],
    )
    op.create_index(
        "idx_watchlist_update_created", "watchlist_update", ["created_at"]
    )


def downgrade() -> None:
    """Drop watchlist_update table."""
    op.drop_index("idx_watchlist_update_created", table_name="watchlist_update")
    op.drop_index("idx_watchlist_update_user_unread", table_name="watchlist_update")
    op.drop_index("idx_watchlist_update_is_read", table_name="watchlist_update")
    op.drop_index("idx_watchlist_update_update_type", table_name="watchlist_update")
    op.drop_index(
        "idx_watchlist_update_watchlist_item_id", table_name="watchlist_update"
    )
    op.drop_index("idx_watchlist_update_user_id", table_name="watchlist_update")
    op.drop_index("idx_watchlist_update_id", table_name="watchlist_update")
    op.drop_table("watchlist_update")

    # Drop enum type
    postgresql.ENUM(name="update_type_enum").drop(op.get_bind(), checkfirst=True)
