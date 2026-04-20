"""skills catalog, user_skills, user_pedagogy

Revision ID: 0002
Revises: 0001
Create Date: 2026-04-19

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

SKILLS_SEED = [
    (
        "avoid_straw_man",
        "Не искажаю чужие аргументы",
        "Старайся пересказывать позицию собеседника честно, без упрощения до «соломенного чучела».",
    ),
    (
        "avoid_ad_hominem",
        "Не перехожу на личности",
        "Критикуй идеи и аргументы, а не человека.",
    ),
    (
        "use_counterexample",
        "Привожу контрпримеры",
        "Используй «например», «представь», «если … то» для проверки мысли.",
    ),
    (
        "ask_clarifying",
        "Задаю уточняющие вопросы",
        "Формулируй вопросы «что именно», «почему», «как ты это видишь».",
    ),
    (
        "structure_argument",
        "Строю связные аргументы",
        "Связывай тезис и основание: «потому что», «следовательно», «таким образом».",
    ),
    (
        "logical_consistency",
        "Соблюдаю логику",
        "Проверяй, что выводы не противоречат тому, что ты уже сказал(а).",
    ),
]


def upgrade() -> None:
    op.create_table(
        "skills",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("skill_id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("default_level", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_skills_skill_id", "skills", ["skill_id"], unique=True)

    op.create_table(
        "user_pedagogy",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("current_difficulty", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("total_deep_responses", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_shallow_responses", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("fallacy_counts", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("last_active_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("logic_check_counter", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
    )

    op.create_table(
        "user_skills",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("skill_id", sa.String(length=64), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_updated", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.skill_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "skill_id"),
    )

    skills_table = sa.table(
        "skills",
        sa.column("skill_id", sa.String),
        sa.column("name", sa.String),
        sa.column("description", sa.Text),
        sa.column("default_level", sa.Integer),
    )
    op.bulk_insert(
        skills_table,
        [
            {
                "skill_id": s[0],
                "name": s[1],
                "description": s[2],
                "default_level": 0,
            }
            for s in SKILLS_SEED
        ],
    )

    conn = op.get_bind()
    users = conn.execute(sa.text("SELECT id FROM users")).fetchall()
    for (uid,) in users:
        conn.execute(
            sa.text(
                """
                INSERT INTO user_pedagogy (
                    user_id, current_difficulty, total_deep_responses,
                    total_shallow_responses, fallacy_counts, last_active_at, logic_check_counter
                )
                VALUES (
                    :uid, 1, 0, 0, '{}', CURRENT_TIMESTAMP, 0
                )
                """
            ),
            {"uid": uid},
        )
        for sid, _, _ in SKILLS_SEED:
            conn.execute(
                sa.text(
                    """
                    INSERT INTO user_skills (user_id, skill_id, level, last_updated)
                    VALUES (:uid, :sid, 0, CURRENT_TIMESTAMP)
                    """
                ),
                {"uid": uid, "sid": sid},
            )


def downgrade() -> None:
    op.drop_table("user_skills")
    op.drop_table("user_pedagogy")
    op.drop_index("ix_skills_skill_id", table_name="skills")
    op.drop_table("skills")
