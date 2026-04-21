"""message client ids for retry deduplication

Revision ID: 0006
Revises: 0005
Create Date: 2026-04-22

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("messages")}
    if "client_message_id" not in columns:
        op.add_column("messages", sa.Column("client_message_id", sa.String(length=64), nullable=True))

    indexes = {idx["name"] for idx in inspector.get_indexes("messages")}
    uniques = {uc["name"] for uc in inspector.get_unique_constraints("messages")}
    target = "uq_messages_conversation_client_message_id"
    if target not in indexes and target not in uniques:
        op.create_index(
            target,
            "messages",
            ["conversation_id", "client_message_id"],
            unique=True,
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    indexes = {idx["name"] for idx in inspector.get_indexes("messages")}
    if "uq_messages_conversation_client_message_id" in indexes:
        op.drop_index("uq_messages_conversation_client_message_id", table_name="messages")
    columns = {col["name"] for col in inspector.get_columns("messages")}
    if "client_message_id" in columns:
        op.drop_column("messages", "client_message_id")
