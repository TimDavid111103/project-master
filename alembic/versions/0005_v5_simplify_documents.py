"""v5: simplify documents table — remove metadata, hierarchy, and taxonomy columns

Revision ID: 0005
Revises: 0004
Create Date: 2026-05-23

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("documents", "category")
    op.drop_column("documents", "concept_tags")
    op.drop_column("documents", "parent_id")
    op.drop_column("documents", "chunk_level")
    op.drop_column("documents", "context_summary")


def downgrade() -> None:
    # Not worth restoring — re-ingest from corpus instead
    pass
