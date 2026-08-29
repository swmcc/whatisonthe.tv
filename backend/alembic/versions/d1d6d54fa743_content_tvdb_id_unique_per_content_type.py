"""Make content.tvdb_id unique per content_type, not globally

TVDB movie and series IDs are separate namespaces, so the same number can
legitimately refer to both a movie and a series. Constraint changes only —
no rows are modified or deleted.

Revision ID: d1d6d54fa743
Revises: c7d5e1f92a03
Create Date: 2026-08-29 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'd1d6d54fa743'
down_revision: Union[str, None] = 'c7d5e1f92a03'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Replace the global unique index on tvdb_id with a plain lookup index
    # plus a composite unique constraint on (tvdb_id, content_type)
    op.drop_index('ix_content_tvdb_id', table_name='content')
    op.create_index('ix_content_tvdb_id', 'content', ['tvdb_id'], unique=False)
    op.create_unique_constraint(
        'uq_content_tvdb_id_content_type', 'content', ['tvdb_id', 'content_type']
    )


def downgrade() -> None:
    # Fails if a movie and a series now share a tvdb_id — resolve those rows
    # manually before downgrading
    op.drop_constraint('uq_content_tvdb_id_content_type', 'content', type_='unique')
    op.drop_index('ix_content_tvdb_id', table_name='content')
    op.create_index('ix_content_tvdb_id', 'content', ['tvdb_id'], unique=True)
