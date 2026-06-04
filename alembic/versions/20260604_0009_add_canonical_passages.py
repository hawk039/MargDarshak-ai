"""add canonical passages

Revision ID: 20260604_0009
Revises: 20260601_0008
Create Date: 2026-06-04 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260604_0009"
down_revision: str | None = "20260601_0008"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    """Create canonical_passages table for Upanishad pilot ingestion."""

    op.create_table(
        "canonical_passages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_document_id", sa.Integer(), nullable=False),
        sa.Column("upanishad_name", sa.String(length=100), nullable=False),
        sa.Column("chapter", sa.String(length=50), nullable=True),
        sa.Column("section", sa.String(length=100), nullable=True),
        sa.Column("passage_number", sa.String(length=50), nullable=False),
        sa.Column("speaker", sa.String(length=100), nullable=True),
        sa.Column("original_text", sa.Text(), nullable=True),
        sa.Column("english_translation", sa.Text(), nullable=False),
        sa.Column("commentary_text", sa.Text(), nullable=True),
        sa.Column("page_reference", sa.String(length=100), nullable=True),
        sa.Column("is_valid", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["source_document_id"],
            ["source_documents.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_canonical_passages_id"), "canonical_passages", ["id"], unique=False)
    op.create_index(
        op.f("ix_canonical_passages_source_document_id"),
        "canonical_passages",
        ["source_document_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_canonical_passages_upanishad_name"),
        "canonical_passages",
        ["upanishad_name"],
        unique=False,
    )
    op.create_index(
        op.f("ix_canonical_passages_chapter"),
        "canonical_passages",
        ["chapter"],
        unique=False,
    )


def downgrade() -> None:
    """Drop canonical_passages table."""

    op.drop_index(op.f("ix_canonical_passages_chapter"), table_name="canonical_passages")
    op.drop_index(op.f("ix_canonical_passages_upanishad_name"), table_name="canonical_passages")
    op.drop_index(op.f("ix_canonical_passages_source_document_id"), table_name="canonical_passages")
    op.drop_index(op.f("ix_canonical_passages_id"), table_name="canonical_passages")
    op.drop_table("canonical_passages")
