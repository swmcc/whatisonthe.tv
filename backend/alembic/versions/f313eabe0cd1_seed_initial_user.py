"""Seed initial user

Revision ID: f313eabe0cd1
Revises: 5df5097e6ed6
Create Date: 2025-11-08 08:36:47.254640

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f313eabe0cd1'
down_revision: Union[str, None] = '5df5097e6ed6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Seed initial user."""
    from datetime import datetime

    # Create users table reference
    users_table = sa.table(
        'users',
        sa.column('email', sa.String),
        sa.column('first_name', sa.String),
        sa.column('last_name', sa.String),
        sa.column('hashed_password', sa.String),
        sa.column('created_at', sa.DateTime),
        sa.column('updated_at', sa.DateTime),
    )

    now = datetime.utcnow()

    # Insert initial user with pre-hashed password (password5)
    op.bulk_insert(
        users_table,
        [
            {
                'email': 'me@swm.cc',
                'first_name': 'Admin',
                'last_name': 'User',
                'hashed_password': '$2b$12$3ijWQk7xIrAn2.nPLy4qNOpF4Sp3ADPEjmdOmXaipxJUdxeJIGjIS',
                'created_at': now,
                'updated_at': now,
            }
        ]
    )


def downgrade() -> None:
    """Remove seeded user."""
    op.execute("DELETE FROM users WHERE email = 'me@swm.cc'")
