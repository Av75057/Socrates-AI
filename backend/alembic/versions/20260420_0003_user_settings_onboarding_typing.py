"""user_settings: onboarding + typing indicator

Revision ID: 0003
Revises: 0002
Create Date: 2026-04-20

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "user_settings",
        sa.Column("has_seen_onboarding", sa.Boolean(), nullable=False, server_default="0"),
    )
    op.add_column(
        "user_settings",
        sa.Column("show_typing_indicator", sa.Boolean(), nullable=False, server_default="1"),
    )


def downgrade() -> None:
    op.drop_column("user_settings", "show_typing_indicator")
    op.drop_column("user_settings", "has_seen_onboarding")
