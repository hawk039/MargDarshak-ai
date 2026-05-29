"""Add principle quality fields to wisdom entries."""

from alembic import op
import sqlalchemy as sa


revision = "20260530_0006"
down_revision = "20260530_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add principle quality fields to wisdom entries."""

    op.add_column("wisdom_entries", sa.Column("principle_quality_score", sa.Float(), nullable=True))
    op.add_column(
        "wisdom_entries",
        sa.Column("principle_status", sa.String(length=50), nullable=False, server_default="needs_review"),
    )


def downgrade() -> None:
    """Remove principle quality fields from wisdom entries."""

    op.drop_column("wisdom_entries", "principle_status")
    op.drop_column("wisdom_entries", "principle_quality_score")
