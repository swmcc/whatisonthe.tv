"""Add watchlist_content_snapshot table

Revision ID: 951a59832cf7
Revises: b3e8f2a94c71
Create Date: 2026-03-15 22:11:15.268672

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '951a59832cf7'
down_revision: Union[str, None] = 'b3e8f2a94c71'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('watchlist_content_snapshot',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('watchlist_item_id', sa.Integer(), nullable=False),
        sa.Column('person_tvdb_id', sa.Integer(), nullable=False),
        sa.Column('role_type', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['watchlist_item_id'], ['watchlist.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('watchlist_item_id', 'person_tvdb_id', 'role_type', name='uq_watchlist_content_snapshot_item_person_role')
    )
    op.create_index('idx_watchlist_content_snapshot_item_lookup', 'watchlist_content_snapshot', ['watchlist_item_id', 'person_tvdb_id', 'role_type'], unique=False)
    op.create_index(op.f('ix_watchlist_content_snapshot_id'), 'watchlist_content_snapshot', ['id'], unique=False)
    op.create_index(op.f('ix_watchlist_content_snapshot_person_tvdb_id'), 'watchlist_content_snapshot', ['person_tvdb_id'], unique=False)
    op.create_index(op.f('ix_watchlist_content_snapshot_watchlist_item_id'), 'watchlist_content_snapshot', ['watchlist_item_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_watchlist_content_snapshot_watchlist_item_id'), table_name='watchlist_content_snapshot')
    op.drop_index(op.f('ix_watchlist_content_snapshot_person_tvdb_id'), table_name='watchlist_content_snapshot')
    op.drop_index(op.f('ix_watchlist_content_snapshot_id'), table_name='watchlist_content_snapshot')
    op.drop_index('idx_watchlist_content_snapshot_item_lookup', table_name='watchlist_content_snapshot')
    op.drop_table('watchlist_content_snapshot')
