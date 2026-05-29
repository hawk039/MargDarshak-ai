"""Add canonical verses table."""

from alembic import op
import sqlalchemy as sa


revision = "20260530_0005"
down_revision = "20260530_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the canonical verses table."""

    op.create_table(
        "canonical_verses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_document_id", sa.Integer(), nullable=False),
        sa.Column("chapter_number", sa.Integer(), nullable=False),
        sa.Column("verse_number", sa.String(length=50), nullable=False),
        sa.Column("speaker", sa.String(length=100), nullable=True),
        sa.Column("sanskrit_text", sa.Text(), nullable=True),
        sa.Column("transliteration", sa.Text(), nullable=True),
        sa.Column("english_translation", sa.Text(), nullable=False),
        sa.Column("commentary", sa.Text(), nullable=True),
        sa.Column("page_reference", sa.String(length=100), nullable=True),
        sa.Column("is_valid", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["source_document_id"],
            ["source_documents.id"],
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "source_document_id",
            "verse_number",
            name="uq_canonical_verses_source_document_verse",
        ),
    )
    op.create_index("ix_canonical_verses_id", "canonical_verses", ["id"], unique=False)
    op.create_index(
        "ix_canonical_verses_source_document_id",
        "canonical_verses",
        ["source_document_id"],
        unique=False,
    )
    op.create_index(
        "ix_canonical_verses_chapter_number",
        "canonical_verses",
        ["chapter_number"],
        unique=False,
    )


def downgrade() -> None:
    """Drop the canonical verses table."""

    op.drop_index("ix_canonical_verses_chapter_number", table_name="canonical_verses")
    op.drop_index("ix_canonical_verses_source_document_id", table_name="canonical_verses")
    op.drop_index("ix_canonical_verses_id", table_name="canonical_verses")
    op.drop_table("canonical_verses")
