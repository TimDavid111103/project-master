"""v2: memory storage tables, hierarchical chunking columns, diskann indexes

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-21

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # pgvectorscale extension (CASCADE also installs pgvector if absent)
    op.execute("CREATE EXTENSION IF NOT EXISTS vectorscale CASCADE")

    # -------------------------------------------------------------------------
    # projects
    # -------------------------------------------------------------------------
    op.create_table(
        "projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # -------------------------------------------------------------------------
    # raw_prompts
    # -------------------------------------------------------------------------
    op.create_table(
        "raw_prompts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.execute("ALTER TABLE raw_prompts ADD COLUMN embedding vector(1536)")
    op.create_index("ix_raw_prompts_project_id", "raw_prompts", ["project_id"])

    # -------------------------------------------------------------------------
    # qa_pairs
    # -------------------------------------------------------------------------
    op.create_table(
        "qa_pairs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("answer_text", sa.Text(), nullable=False),
        sa.Column(
            "session_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.execute("ALTER TABLE qa_pairs ADD COLUMN embedding vector(1536)")
    op.create_index("ix_qa_pairs_project_id", "qa_pairs", ["project_id"])

    # -------------------------------------------------------------------------
    # prompt_analyses
    # -------------------------------------------------------------------------
    op.create_table(
        "prompt_analyses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("original_prompt", sa.Text(), nullable=False),
        sa.Column("intent_accuracy_grade", sa.String(1), nullable=False),
        sa.Column("intent_accuracy_explanation", sa.Text(), nullable=False),
        sa.Column("technical_language_grade", sa.String(1), nullable=False),
        sa.Column("technical_language_explanation", sa.Text(), nullable=False),
        sa.Column("standards_alignment_grade", sa.String(1), nullable=False),
        sa.Column("standards_alignment_explanation", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.execute("ALTER TABLE prompt_analyses ADD COLUMN embedding vector(1536)")
    op.create_index(
        "ix_prompt_analyses_project_id", "prompt_analyses", ["project_id"]
    )

    # -------------------------------------------------------------------------
    # documents: add hierarchical chunking columns
    # -------------------------------------------------------------------------
    op.add_column(
        "documents",
        sa.Column("parent_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "documents",
        sa.Column(
            "chunk_level", sa.String(16), server_default="chunk", nullable=False
        ),
    )
    op.add_column(
        "documents",
        sa.Column("context_summary", sa.Text(), nullable=True),
    )
    op.create_foreign_key(
        "fk_documents_parent_id",
        "documents",
        "documents",
        ["parent_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_documents_parent_id", "documents", ["parent_id"])

    # -------------------------------------------------------------------------
    # DiskANN indexes (replace HNSW on documents; add to memory tables)
    # -------------------------------------------------------------------------
    op.execute("DROP INDEX IF EXISTS ix_documents_embedding_hnsw")

    op.execute(
        "CREATE INDEX ix_documents_embedding_diskann "
        "ON documents USING diskann (embedding vector_cosine_ops)"
    )
    op.execute(
        "CREATE INDEX ix_raw_prompts_embedding_diskann "
        "ON raw_prompts USING diskann (embedding vector_cosine_ops) "
        "WHERE embedding IS NOT NULL"
    )
    op.execute(
        "CREATE INDEX ix_qa_pairs_embedding_diskann "
        "ON qa_pairs USING diskann (embedding vector_cosine_ops) "
        "WHERE embedding IS NOT NULL"
    )
    op.execute(
        "CREATE INDEX ix_prompt_analyses_embedding_diskann "
        "ON prompt_analyses USING diskann (embedding vector_cosine_ops) "
        "WHERE embedding IS NOT NULL"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_prompt_analyses_embedding_diskann")
    op.execute("DROP INDEX IF EXISTS ix_qa_pairs_embedding_diskann")
    op.execute("DROP INDEX IF EXISTS ix_raw_prompts_embedding_diskann")
    op.execute("DROP INDEX IF EXISTS ix_documents_embedding_diskann")

    op.execute(
        """
        CREATE INDEX ix_documents_embedding_hnsw
        ON documents
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
        """
    )

    op.drop_index("ix_documents_parent_id", table_name="documents")
    op.drop_constraint("fk_documents_parent_id", "documents", type_="foreignkey")
    op.drop_column("documents", "context_summary")
    op.drop_column("documents", "chunk_level")
    op.drop_column("documents", "parent_id")

    op.drop_index("ix_prompt_analyses_project_id", table_name="prompt_analyses")
    op.drop_table("prompt_analyses")

    op.drop_index("ix_qa_pairs_project_id", table_name="qa_pairs")
    op.drop_table("qa_pairs")

    op.drop_index("ix_raw_prompts_project_id", table_name="raw_prompts")
    op.drop_table("raw_prompts")

    op.drop_table("projects")
