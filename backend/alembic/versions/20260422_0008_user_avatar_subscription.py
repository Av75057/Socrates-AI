"""user avatar and subscription fields

Revision ID: 20260422_0008
Revises: 0007
Create Date: 2026-04-22
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260422_0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def _has_column(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    cols = {col["name"] for col in insp.get_columns(table_name)}
    return column_name in cols


def upgrade() -> None:
    if not _has_column("users", "avatar_path"):
        op.add_column("users", sa.Column("avatar_path", sa.String(length=512), nullable=True))
    if not _has_column("users", "subscription_plan"):
        op.add_column(
            "users",
            sa.Column("subscription_plan", sa.String(length=32), nullable=False, server_default="free"),
        )
    if not _has_column("users", "subscription_status"):
        op.add_column(
            "users",
            sa.Column("subscription_status", sa.String(length=32), nullable=False, server_default="active"),
        )
    if not _has_column("users", "subscription_current_period_end"):
        op.add_column("users", sa.Column("subscription_current_period_end", sa.DateTime(timezone=True), nullable=True))

    op.execute("UPDATE users SET subscription_plan = COALESCE(subscription_plan, 'free')")
    op.execute("UPDATE users SET subscription_status = COALESCE(subscription_status, 'active')")


def downgrade() -> None:
    if _has_column("users", "subscription_current_period_end"):
        op.drop_column("users", "subscription_current_period_end")
    if _has_column("users", "subscription_status"):
        op.drop_column("users", "subscription_status")
    if _has_column("users", "subscription_plan"):
        op.drop_column("users", "subscription_plan")
    if _has_column("users", "avatar_path"):
        op.drop_column("users", "avatar_path")
