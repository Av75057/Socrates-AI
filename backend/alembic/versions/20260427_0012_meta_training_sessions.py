"""meta training sessions

Revision ID: 20260427_0012
Revises: 20260422_0011
Create Date: 2026-04-27
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260427_0012"
down_revision = "20260422_0011"
branch_labels = None
depends_on = None


def _has_table(table_name: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return table_name in set(insp.get_table_names())


def _has_index(table_name: str, index_name: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    indexes = {idx["name"] for idx in insp.get_indexes(table_name)}
    return index_name in indexes


def upgrade() -> None:
    if not _has_table("meta_training_sessions"):
        op.create_table(
            "meta_training_sessions",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True),
            sa.Column("session_key", sa.String(length=128), nullable=False),
            sa.Column("thesis", sa.Text(), nullable=False),
            sa.Column("topic_slug", sa.String(length=128), nullable=False),
            sa.Column("final_phase", sa.String(length=32), nullable=False, server_default="completed"),
            sa.Column("scores", sa.JSON(), nullable=False, server_default="{}"),
            sa.Column("questions", sa.JSON(), nullable=False, server_default="[]"),
            sa.Column("frames", sa.JSON(), nullable=False, server_default="[]"),
            sa.Column("transcript", sa.JSON(), nullable=False, server_default="[]"),
            sa.Column("reflection_summary", sa.Text(), nullable=True),
            sa.Column("confidence_label", sa.String(length=64), nullable=True),
            sa.Column("awarded_wisdom_points", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("ended_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
    if _has_table("meta_training_sessions") and not _has_index("meta_training_sessions", "ix_meta_training_sessions_user_id"):
        op.create_index("ix_meta_training_sessions_user_id", "meta_training_sessions", ["user_id"], unique=False)
    if _has_table("meta_training_sessions") and not _has_index("meta_training_sessions", "ix_meta_training_sessions_session_key"):
        op.create_index("ix_meta_training_sessions_session_key", "meta_training_sessions", ["session_key"], unique=False)


def downgrade() -> None:
    if _has_table("meta_training_sessions") and _has_index("meta_training_sessions", "ix_meta_training_sessions_session_key"):
        op.drop_index("ix_meta_training_sessions_session_key", table_name="meta_training_sessions")
    if _has_table("meta_training_sessions") and _has_index("meta_training_sessions", "ix_meta_training_sessions_user_id"):
        op.drop_index("ix_meta_training_sessions_user_id", table_name="meta_training_sessions")
    if _has_table("meta_training_sessions"):
        op.drop_table("meta_training_sessions")
