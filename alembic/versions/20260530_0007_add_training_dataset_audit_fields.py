"""add training dataset audit fields

Revision ID: 20260530_0007
Revises: 20260530_0006
Create Date: 2026-05-30 02:15:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260530_0007"
down_revision = "20260530_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add training dataset audit columns."""

    with op.batch_alter_table("training_examples") as batch_op:
        batch_op.add_column(sa.Column("dataset_quality_score", sa.Float(), nullable=True))
        batch_op.add_column(
            sa.Column(
                "dataset_status",
                sa.String(length=50),
                nullable=False,
                server_default="needs_review",
            )
        )
        batch_op.add_column(
            sa.Column(
                "dataset_audit_issues",
                sa.JSON(),
                nullable=False,
                server_default=sa.text("'[]'"),
            )
        )


def downgrade() -> None:
    """Remove training dataset audit columns."""

    with op.batch_alter_table("training_examples") as batch_op:
        batch_op.drop_column("dataset_audit_issues")
        batch_op.drop_column("dataset_status")
        batch_op.drop_column("dataset_quality_score")
