"""Add sync_task_id to content

Revision ID: c8d1e2f3a4b5
Revises: b2f4a7c83d91
Create Date: 2026-03-03 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c8d1e2f3a4b5'
down_revision: Union[str, None] = 'b2f4a7c83d91'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'content',
        sa.Column('sync_task_id', sa.String(255), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('content', 'sync_task_id')
