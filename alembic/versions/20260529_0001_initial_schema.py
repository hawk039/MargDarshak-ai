"""Initial schema for source documents, wisdom entries, and training examples."""

from alembic import op
import sqlalchemy as sa


revision = "20260529_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the initial project tables."""

    op.create_table(
        "source_documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("tradition", sa.String(length=100), nullable=True),
        sa.Column("document_type", sa.String(length=100), nullable=True),
        sa.Column("language", sa.String(length=50), nullable=True),
        sa.Column("author_or_translator", sa.String(length=255), nullable=True),
        sa.Column("source_name", sa.String(length=255), nullable=True),
        sa.Column("file_path", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_source_documents_id", "source_documents", ["id"], unique=False)
    op.create_index("ix_source_documents_language", "source_documents", ["language"], unique=False)
    op.create_index("ix_source_documents_title", "source_documents", ["title"], unique=False)
    op.create_index("ix_source_documents_tradition", "source_documents", ["tradition"], unique=False)

    op.create_table(
        "wisdom_entries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_document_id", sa.Integer(), nullable=False),
        sa.Column("book_title", sa.String(length=255), nullable=True),
        sa.Column("chapter", sa.String(length=100), nullable=True),
        sa.Column("section", sa.String(length=100), nullable=True),
        sa.Column("verse_number", sa.String(length=50), nullable=True),
        sa.Column("original_text", sa.Text(), nullable=False),
        sa.Column("transliteration", sa.Text(), nullable=True),
        sa.Column("translation", sa.Text(), nullable=True),
        sa.Column("commentary", sa.Text(), nullable=True),
        sa.Column("extracted_principle", sa.Text(), nullable=True),
        sa.Column("emotional_tags", sa.JSON(), nullable=False),
        sa.Column("philosophical_tags", sa.JSON(), nullable=False),
        sa.Column("use_cases", sa.JSON(), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["source_document_id"],
            ["source_documents.id"],
            ondelete="CASCADE",
        ),
    )
    op.create_index("ix_wisdom_entries_book_title", "wisdom_entries", ["book_title"], unique=False)
    op.create_index("ix_wisdom_entries_id", "wisdom_entries", ["id"], unique=False)
    op.create_index(
        "ix_wisdom_entries_source_document_id",
        "wisdom_entries",
        ["source_document_id"],
        unique=False,
    )

    op.create_table(
        "training_examples",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("wisdom_entry_id", sa.Integer(), nullable=False),
        sa.Column("user_problem", sa.Text(), nullable=False),
        sa.Column("assistant_response", sa.Text(), nullable=False),
        sa.Column("tone", sa.String(length=100), nullable=True),
        sa.Column("safety_category", sa.String(length=100), nullable=True),
        sa.Column("source_references", sa.JSON(), nullable=False),
        sa.Column("approved_for_finetune", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["wisdom_entry_id"],
            ["wisdom_entries.id"],
            ondelete="CASCADE",
        ),
    )
    op.create_index("ix_training_examples_id", "training_examples", ["id"], unique=False)
    op.create_index(
        "ix_training_examples_wisdom_entry_id",
        "training_examples",
        ["wisdom_entry_id"],
        unique=False,
    )


def downgrade() -> None:
    """Drop the initial project tables."""

    op.drop_index("ix_training_examples_wisdom_entry_id", table_name="training_examples")
    op.drop_index("ix_training_examples_id", table_name="training_examples")
    op.drop_table("training_examples")

    op.drop_index("ix_wisdom_entries_source_document_id", table_name="wisdom_entries")
    op.drop_index("ix_wisdom_entries_id", table_name="wisdom_entries")
    op.drop_index("ix_wisdom_entries_book_title", table_name="wisdom_entries")
    op.drop_table("wisdom_entries")

    op.drop_index("ix_source_documents_tradition", table_name="source_documents")
    op.drop_index("ix_source_documents_title", table_name="source_documents")
    op.drop_index("ix_source_documents_language", table_name="source_documents")
    op.drop_index("ix_source_documents_id", table_name="source_documents")
    op.drop_table("source_documents")
