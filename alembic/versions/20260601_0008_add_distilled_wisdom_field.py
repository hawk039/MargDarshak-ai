"""add distilled wisdom field

Revision ID: 20260601_0008
Revises: 20260530_0007
Create Date: 2026-06-01 16:55:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260601_0008"
down_revision = "20260530_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add distilled wisdom column to wisdom entries."""

    with op.batch_alter_table("wisdom_entries") as batch_op:
        batch_op.add_column(sa.Column("distilled_wisdom", sa.Text(), nullable=True))


def downgrade() -> None:
    """Remove distilled wisdom column from wisdom entries."""

    with op.batch_alter_table("wisdom_entries") as batch_op:
        batch_op.drop_column("distilled_wisdom")
