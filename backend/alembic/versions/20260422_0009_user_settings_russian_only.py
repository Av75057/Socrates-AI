"""add russian_only to user settings

Revision ID: 20260422_0009
Revises: 20260422_0008
Create Date: 2026-04-22
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260422_0009"
down_revision = "20260422_0008"
branch_labels = None
depends_on = None


def _has_column(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    cols = {col["name"] for col in insp.get_columns(table_name)}
    return column_name in cols


def upgrade() -> None:
    if not _has_column("user_settings", "russian_only"):
        op.add_column(
            "user_settings",
            sa.Column("russian_only", sa.Boolean(), nullable=False, server_default=sa.true()),
        )
    op.execute("UPDATE user_settings SET russian_only = 1 WHERE russian_only IS NULL")


def downgrade() -> None:
    if _has_column("user_settings", "russian_only"):
        op.drop_column("user_settings", "russian_only")
