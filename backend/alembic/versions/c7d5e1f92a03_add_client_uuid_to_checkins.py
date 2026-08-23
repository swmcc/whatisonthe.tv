"""Add client_uuid to checkins

Revision ID: c7d5e1f92a03
Revises: 951a59832cf7
Create Date: 2026-08-23 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c7d5e1f92a03'
down_revision: Union[str, None] = '951a59832cf7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add nullable client_uuid column for idempotent check-in creation
    op.add_column(
        'checkins',
        sa.Column('client_uuid', sa.String(36), nullable=True)
    )

    # Unique index; NULLs do not collide in Postgres so existing rows are fine
    op.create_index(
        'ix_checkins_client_uuid', 'checkins', ['client_uuid'], unique=True
    )


def downgrade() -> None:
    op.drop_index('ix_checkins_client_uuid', table_name='checkins')
    op.drop_column('checkins', 'client_uuid')
