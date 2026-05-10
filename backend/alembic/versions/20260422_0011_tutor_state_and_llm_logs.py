"""tutor state and llm logs

Revision ID: 20260422_0011
Revises: 20260422_0010
Create Date: 2026-04-22
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260422_0011"
down_revision = "20260422_0010"
branch_labels = None
depends_on = None


def _has_table(table_name: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return table_name in set(insp.get_table_names())


def _has_column(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return column_name in {col["name"] for col in insp.get_columns(table_name)}


def _has_index(table_name: str, index_name: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    indexes = {idx["name"] for idx in insp.get_indexes(table_name)}
    return index_name in indexes


def upgrade() -> None:
    if _has_table("conversations") and not _has_column("conversations", "tutor_state"):
        op.add_column(
            "conversations",
            sa.Column(
                "tutor_state",
                sa.JSON(),
                nullable=False,
                server_default='{"level": 2, "mode": "friendly", "step": 0, "stuck": false, "last_fallacy": null, "topic": "general", "attempted_concepts": []}',
            ),
        )

    if not _has_table("llm_logs"):
        op.create_table(
            "llm_logs",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("conversation_id", sa.Integer(), sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True),
            sa.Column("system_prompt", sa.Text(), nullable=False),
            sa.Column("user_messages", sa.JSON(), nullable=False, server_default="[]"),
            sa.Column("model_params", sa.JSON(), nullable=False, server_default="{}"),
            sa.Column("raw_response", sa.Text(), nullable=False),
            sa.Column("response_tokens", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("latency_ms", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
    if _has_table("llm_logs") and not _has_index("llm_logs", "ix_llm_logs_conversation_id"):
        op.create_index("ix_llm_logs_conversation_id", "llm_logs", ["conversation_id"], unique=False)
    if _has_table("llm_logs") and not _has_index("llm_logs", "ix_llm_logs_user_id"):
        op.create_index("ix_llm_logs_user_id", "llm_logs", ["user_id"], unique=False)


def downgrade() -> None:
    if _has_table("llm_logs") and _has_index("llm_logs", "ix_llm_logs_user_id"):
        op.drop_index("ix_llm_logs_user_id", table_name="llm_logs")
    if _has_table("llm_logs") and _has_index("llm_logs", "ix_llm_logs_conversation_id"):
        op.drop_index("ix_llm_logs_conversation_id", table_name="llm_logs")
    if _has_table("llm_logs"):
        op.drop_table("llm_logs")
    if _has_table("conversations") and _has_column("conversations", "tutor_state"):
        op.drop_column("conversations", "tutor_state")
