"""v3: project setup flow, intent translation replaces graded analysis

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-22

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -------------------------------------------------------------------------
    # projects: rename summary -> rough_idea, add nullable definition column
    # -------------------------------------------------------------------------
    op.alter_column("projects", "summary", new_column_name="rough_idea")
    op.add_column("projects", sa.Column("definition", sa.Text(), nullable=True))

    # -------------------------------------------------------------------------
    # prompt_analyses: replace six grade/explanation columns with three
    # intent translation columns
    # -------------------------------------------------------------------------
    op.drop_column("prompt_analyses", "intent_accuracy_grade")
    op.drop_column("prompt_analyses", "intent_accuracy_explanation")
    op.drop_column("prompt_analyses", "technical_language_grade")
    op.drop_column("prompt_analyses", "technical_language_explanation")
    op.drop_column("prompt_analyses", "standards_alignment_grade")
    op.drop_column("prompt_analyses", "standards_alignment_explanation")

    op.add_column(
        "prompt_analyses",
        sa.Column(
            "what_the_prompt_instructs",
            sa.Text(),
            nullable=False,
            server_default="",
        ),
    )
    op.add_column(
        "prompt_analyses",
        sa.Column(
            "assumptions_made",
            sa.Text(),
            nullable=False,
            server_default="[]",
        ),
    )
    op.add_column(
        "prompt_analyses",
        sa.Column(
            "potential_gaps",
            sa.Text(),
            nullable=False,
            server_default="[]",
        ),
    )


def downgrade() -> None:
    op.drop_column("prompt_analyses", "potential_gaps")
    op.drop_column("prompt_analyses", "assumptions_made")
    op.drop_column("prompt_analyses", "what_the_prompt_instructs")

    op.add_column(
        "prompt_analyses",
        sa.Column("standards_alignment_explanation", sa.Text(), nullable=False, server_default=""),
    )
    op.add_column(
        "prompt_analyses",
        sa.Column("standards_alignment_grade", sa.String(1), nullable=False, server_default="F"),
    )
    op.add_column(
        "prompt_analyses",
        sa.Column("technical_language_explanation", sa.Text(), nullable=False, server_default=""),
    )
    op.add_column(
        "prompt_analyses",
        sa.Column("technical_language_grade", sa.String(1), nullable=False, server_default="F"),
    )
    op.add_column(
        "prompt_analyses",
        sa.Column("intent_accuracy_explanation", sa.Text(), nullable=False, server_default=""),
    )
    op.add_column(
        "prompt_analyses",
        sa.Column("intent_accuracy_grade", sa.String(1), nullable=False, server_default="F"),
    )

    op.drop_column("projects", "definition")
    op.alter_column("projects", "rough_idea", new_column_name="summary")
