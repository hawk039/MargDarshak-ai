"""Add quality reviews table."""

from alembic import op
import sqlalchemy as sa


revision = "20260530_0004"
down_revision = "20260529_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the quality reviews table."""

    op.create_table(
        "quality_reviews",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("wisdom_entry_id", sa.Integer(), nullable=False),
        sa.Column("quality_score", sa.Integer(), nullable=False),
        sa.Column("validation_status", sa.String(length=50), nullable=False),
        sa.Column("issues", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["wisdom_entry_id"],
            ["wisdom_entries.id"],
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "wisdom_entry_id",
            name="uq_quality_reviews_wisdom_entry_id",
        ),
    )
    op.create_index("ix_quality_reviews_id", "quality_reviews", ["id"], unique=False)
    op.create_index(
        "ix_quality_reviews_wisdom_entry_id",
        "quality_reviews",
        ["wisdom_entry_id"],
        unique=False,
    )


def downgrade() -> None:
    """Drop the quality reviews table."""

    op.drop_index("ix_quality_reviews_wisdom_entry_id", table_name="quality_reviews")
    op.drop_index("ix_quality_reviews_id", table_name="quality_reviews")
    op.drop_table("quality_reviews")
