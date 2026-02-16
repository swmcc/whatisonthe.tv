"""Add focus column to checkins

Revision ID: b2f4a7c83d91
Revises: a1c69d1487a8
Create Date: 2026-02-16 17:24:14.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2f4a7c83d91'
down_revision: Union[str, None] = 'a1c69d1487a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create the focus enum type
    focus_enum = sa.Enum('focused', 'distracted', 'background', 'sleep', name='focuslevel')
    focus_enum.create(op.get_bind(), checkfirst=True)

    # Add focus column to checkins table
    op.add_column(
        'checkins',
        sa.Column('focus', focus_enum, nullable=True)
    )


def downgrade() -> None:
    # Drop the focus column
    op.drop_column('checkins', 'focus')

    # Drop the enum type
    sa.Enum(name='focuslevel').drop(op.get_bind(), checkfirst=True)
