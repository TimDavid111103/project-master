"""initial: vector extension + documents table + indexes

Revision ID: 0001
Revises:
Create Date: 2026-04-21

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_file", sa.String(512), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("category", sa.String(128), nullable=False),
        sa.Column("concept_tags", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("embedding", sa.Text(), nullable=False),  # pgvector type applied below
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # Re-create the embedding column with proper vector type after extension exists
    op.execute("ALTER TABLE documents DROP COLUMN embedding")
    op.execute("ALTER TABLE documents ADD COLUMN embedding vector(1536) NOT NULL")

    op.create_index("ix_documents_category", "documents", ["category"])
    op.create_index(
        "ix_documents_concept_tags_gin",
        "documents",
        ["concept_tags"],
        postgresql_using="gin",
    )
    op.execute(
        """
        CREATE INDEX ix_documents_embedding_hnsw
        ON documents
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
        """
    )


def downgrade() -> None:
    op.drop_table("documents")
    op.execute("DROP EXTENSION IF EXISTS vector")
