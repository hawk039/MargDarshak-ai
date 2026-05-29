"""Add structured document chunks table."""

from alembic import op
import sqlalchemy as sa


revision = "20260529_0003"
down_revision = "20260529_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the structured document chunks table."""

    op.create_table(
        "document_chunks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_document_id", sa.Integer(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("chapter", sa.String(length=100), nullable=True),
        sa.Column("section_title", sa.String(length=255), nullable=True),
        sa.Column("verse_number", sa.String(length=50), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("content_type", sa.String(length=50), nullable=False),
        sa.Column("page_reference", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["source_document_id"],
            ["source_documents.id"],
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "source_document_id",
            "chunk_index",
            name="uq_document_chunks_source_chunk",
        ),
    )
    op.create_index("ix_document_chunks_id", "document_chunks", ["id"], unique=False)
    op.create_index(
        "ix_document_chunks_source_document_id",
        "document_chunks",
        ["source_document_id"],
        unique=False,
    )


def downgrade() -> None:
    """Drop the structured document chunks table."""

    op.drop_index("ix_document_chunks_source_document_id", table_name="document_chunks")
    op.drop_index("ix_document_chunks_id", table_name="document_chunks")
    op.drop_table("document_chunks")
