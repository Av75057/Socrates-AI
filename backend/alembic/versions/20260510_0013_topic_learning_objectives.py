"""topic learning objectives and mastery progress

Revision ID: 20260510_0013
Revises: 20260427_0012
Create Date: 2026-05-10
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260510_0013"
down_revision = "20260427_0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "topics",
        sa.Column("learning_objectives", sa.JSON(), nullable=False, server_default="[]"),
    )
    op.add_column(
        "user_topic_progress",
        sa.Column("mastery_score", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "user_topic_progress",
        sa.Column("goals_state", sa.JSON(), nullable=False, server_default="[]"),
    )
    op.add_column(
        "user_topic_progress",
        sa.Column("last_assessed_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("user_topic_progress", "last_assessed_at")
    op.drop_column("user_topic_progress", "goals_state")
    op.drop_column("user_topic_progress", "mastery_score")
    op.drop_column("topics", "learning_objectives")
