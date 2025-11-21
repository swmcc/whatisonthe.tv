"""Add username to users table

Revision ID: a1c69d1487a8
Revises: a1533b94a24c
Create Date: 2025-11-21 21:49:38.062796

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1c69d1487a8'
down_revision: Union[str, None] = 'a1533b94a24c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add username column
    op.add_column('users', sa.Column('username', sa.String(length=50), nullable=True))

    # Create unique index on username
    op.create_index('ix_users_username', 'users', ['username'], unique=True)


def downgrade() -> None:
    # Drop index
    op.drop_index('ix_users_username', table_name='users')

    # Drop username column
    op.drop_column('users', 'username')
