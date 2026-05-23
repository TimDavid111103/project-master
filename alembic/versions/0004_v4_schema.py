"""v4: project planning pipeline — replace prompt analysis with plan + tech stack

Revision ID: 0004
Revises: 0003
Create Date: 2026-05-23

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns to projects
    op.add_column("projects", sa.Column("project_plan_json", sa.Text(), nullable=True))
    op.add_column("projects", sa.Column("tech_stack_json", sa.Text(), nullable=True))

    # Remove old definition column from projects
    op.drop_column("projects", "definition")

    # Drop old tables no longer needed
    op.drop_table("prompt_analyses")
    op.drop_table("qa_pairs")
    op.drop_table("raw_prompts")


def downgrade() -> None:
    op.add_column("projects", sa.Column("definition", sa.Text(), nullable=True))
    op.drop_column("projects", "tech_stack_json")
    op.drop_column("projects", "project_plan_json")
