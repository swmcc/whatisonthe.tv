"""Add watchlist table

Revision ID: c8d2f3a91b47
Revises: b2f4a7c83d91
Create Date: 2026-03-06 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c8d2f3a91b47'
down_revision: Union[str, None] = 'b2f4a7c83d91'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create watchlist table with inline enum creation
    op.create_table(
        'watchlist',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('item_type', sa.Enum('content', 'person', name='watchlist_item_type_enum', create_constraint=True), nullable=False),
        sa.Column('content_id', sa.Integer(), nullable=True),
        sa.Column('person_id', sa.Integer(), nullable=True),
        sa.Column('person_role_filter', sa.Enum('any', 'actor', 'director', name='person_role_filter_enum', create_constraint=True), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['content_id'], ['content.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['person_id'], ['person.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'content_id', name='uq_watchlist_user_content'),
        sa.UniqueConstraint('user_id', 'person_id', name='uq_watchlist_user_person'),
    )

    # Create indexes
    op.create_index(op.f('ix_watchlist_id'), 'watchlist', ['id'], unique=False)
    op.create_index(op.f('ix_watchlist_user_id'), 'watchlist', ['user_id'], unique=False)
    op.create_index(op.f('ix_watchlist_item_type'), 'watchlist', ['item_type'], unique=False)
    op.create_index(op.f('ix_watchlist_content_id'), 'watchlist', ['content_id'], unique=False)
    op.create_index(op.f('ix_watchlist_person_id'), 'watchlist', ['person_id'], unique=False)
    op.create_index('idx_watchlist_user_item_type', 'watchlist', ['user_id', 'item_type'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_watchlist_user_item_type', table_name='watchlist')
    op.drop_index(op.f('ix_watchlist_person_id'), table_name='watchlist')
    op.drop_index(op.f('ix_watchlist_content_id'), table_name='watchlist')
    op.drop_index(op.f('ix_watchlist_item_type'), table_name='watchlist')
    op.drop_index(op.f('ix_watchlist_user_id'), table_name='watchlist')
    op.drop_index(op.f('ix_watchlist_id'), table_name='watchlist')

    # Drop table
    op.drop_table('watchlist')

    # Drop enum types
    sa.Enum(name='person_role_filter_enum').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='watchlist_item_type_enum').drop(op.get_bind(), checkfirst=True)
