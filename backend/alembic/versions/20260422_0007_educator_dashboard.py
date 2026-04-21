"""educator dashboard schema

Revision ID: 0007
Revises: 0006
Create Date: 2026-04-22

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = set(inspector.get_table_names())

    if "classes" not in tables:
        op.create_table(
            "classes",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("educator_id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("description", sa.String(length=512), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["educator_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        tables.add("classes")
    class_indexes = {idx["name"] for idx in inspector.get_indexes("classes")} if "classes" in tables else set()
    if "ix_classes_educator_id" not in class_indexes:
        op.create_index("ix_classes_educator_id", "classes", ["educator_id"], unique=False)

    if "class_students" not in tables:
        op.create_table(
            "class_students",
            sa.Column("class_id", sa.Integer(), nullable=False),
            sa.Column("student_id", sa.Integer(), nullable=False),
            sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["class_id"], ["classes.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["student_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("class_id", "student_id"),
        )
        tables.add("class_students")

    if "assignments" not in tables:
        op.create_table(
            "assignments",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("class_id", sa.Integer(), nullable=False),
            sa.Column("title", sa.String(length=255), nullable=False),
            sa.Column("prompt", sa.Text(), nullable=False),
            sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["class_id"], ["classes.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        tables.add("assignments")
    assignment_indexes = {idx["name"] for idx in inspector.get_indexes("assignments")} if "assignments" in tables else set()
    if "ix_assignments_class_id" not in assignment_indexes:
        op.create_index("ix_assignments_class_id", "assignments", ["class_id"], unique=False)

    conversation_columns = {col["name"] for col in inspector.get_columns("conversations")}
    if "assignment_id" not in conversation_columns:
        op.add_column("conversations", sa.Column("assignment_id", sa.Integer(), nullable=True))
    conversation_indexes = {idx["name"] for idx in inspector.get_indexes("conversations")}
    if "ix_conversations_assignment_id" not in conversation_indexes:
        op.create_index("ix_conversations_assignment_id", "conversations", ["assignment_id"], unique=False)

    if bind.dialect.name != "sqlite":
        foreign_keys = {fk["name"] for fk in inspector.get_foreign_keys("conversations")}
        if "fk_conversations_assignment_id_assignments" not in foreign_keys:
            op.create_foreign_key(
                "fk_conversations_assignment_id_assignments",
                "conversations",
                "assignments",
                ["assignment_id"],
                ["id"],
                ondelete="SET NULL",
            )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if bind.dialect.name != "sqlite":
        foreign_keys = {fk["name"] for fk in inspector.get_foreign_keys("conversations")}
        if "fk_conversations_assignment_id_assignments" in foreign_keys:
            op.drop_constraint("fk_conversations_assignment_id_assignments", "conversations", type_="foreignkey")
    conversation_indexes = {idx["name"] for idx in inspector.get_indexes("conversations")}
    if "ix_conversations_assignment_id" in conversation_indexes:
        op.drop_index("ix_conversations_assignment_id", table_name="conversations")
    conversation_columns = {col["name"] for col in inspector.get_columns("conversations")}
    if "assignment_id" in conversation_columns:
        op.drop_column("conversations", "assignment_id")
    tables = set(inspector.get_table_names())
    if "assignments" in tables:
        assignment_indexes = {idx["name"] for idx in inspector.get_indexes("assignments")}
        if "ix_assignments_class_id" in assignment_indexes:
            op.drop_index("ix_assignments_class_id", table_name="assignments")
        op.drop_table("assignments")
    if "class_students" in tables:
        op.drop_table("class_students")
    if "classes" in tables:
        class_indexes = {idx["name"] for idx in inspector.get_indexes("classes")}
        if "ix_classes_educator_id" in class_indexes:
            op.drop_index("ix_classes_educator_id", table_name="classes")
        op.drop_table("classes")
