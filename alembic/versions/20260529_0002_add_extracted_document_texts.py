"""Add extracted document texts table."""

from alembic import op
import sqlalchemy as sa


revision = "20260529_0002"
down_revision = "20260529_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the extracted document text storage table."""

    op.create_table(
        "extracted_document_texts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_document_id", sa.Integer(), nullable=False, unique=True),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("page_count", sa.Integer(), nullable=False),
        sa.Column("extraction_status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["source_document_id"],
            ["source_documents.id"],
            ondelete="CASCADE",
        ),
    )
    op.create_index("ix_extracted_document_texts_id", "extracted_document_texts", ["id"], unique=False)
    op.create_index(
        "ix_extracted_document_texts_source_document_id",
        "extracted_document_texts",
        ["source_document_id"],
        unique=True,
    )


def downgrade() -> None:
    """Drop the extracted document text storage table."""

    op.drop_index(
        "ix_extracted_document_texts_source_document_id",
        table_name="extracted_document_texts",
    )
    op.drop_index("ix_extracted_document_texts_id", table_name="extracted_document_texts")
    op.drop_table("extracted_document_texts")
