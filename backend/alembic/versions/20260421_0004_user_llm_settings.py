"""user_settings: локальная LLM (OpenAI-совместимый API)

Revision ID: 0004
Revises: 0003
Create Date: 2026-04-21

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("user_settings") as batch:
        batch.add_column(sa.Column("llm_base_url", sa.String(512), nullable=True))
        batch.add_column(sa.Column("llm_api_key", sa.Text(), nullable=True))
        batch.add_column(sa.Column("llm_model_name", sa.String(256), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("user_settings") as batch:
        batch.drop_column("llm_model_name")
        batch.drop_column("llm_api_key")
        batch.drop_column("llm_base_url")
