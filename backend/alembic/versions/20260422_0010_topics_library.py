"""topics library

Revision ID: 20260422_0010
Revises: 20260422_0009
Create Date: 2026-04-22
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260422_0010"
down_revision = "20260422_0009"
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
    if not _has_table("topics"):
        op.create_table(
            "topics",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("title", sa.String(length=255), nullable=False),
            sa.Column("description", sa.String(length=512), nullable=True),
            sa.Column("initial_prompt", sa.Text(), nullable=False),
            sa.Column("difficulty", sa.Integer(), nullable=False, server_default="2"),
            sa.Column("tags", sa.JSON(), nullable=False, server_default="[]"),
            sa.Column("is_premium", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("usage_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        )
    if not _has_index("topics", "ix_topics_title"):
        op.create_index("ix_topics_title", "topics", ["title"], unique=False)
    if not _has_index("topics", "ix_topics_created_by"):
        op.create_index("ix_topics_created_by", "topics", ["created_by"], unique=False)

    if not _has_table("user_topic_progress"):
        op.create_table(
            "user_topic_progress",
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("topic_id", sa.Integer(), sa.ForeignKey("topics.id", ondelete="CASCADE"), nullable=False),
            sa.Column("completed", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("last_used", sa.DateTime(timezone=True), nullable=True),
            sa.Column("rating", sa.Integer(), nullable=True),
            sa.PrimaryKeyConstraint("user_id", "topic_id"),
        )


def downgrade() -> None:
    if _has_table("user_topic_progress"):
        op.drop_table("user_topic_progress")
    if _has_index("topics", "ix_topics_created_by"):
        op.drop_index("ix_topics_created_by", table_name="topics")
    if _has_index("topics", "ix_topics_title"):
        op.drop_index("ix_topics_title", table_name="topics")
    if _has_table("topics"):
        op.drop_table("topics")
