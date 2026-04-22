"""ORM-модели PostgreSQL / SQLite."""

from __future__ import annotations

import enum
from datetime import date, datetime, timezone

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy import JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


JSONType = JSON


class UserRole(str, enum.Enum):
    user = "user"
    admin = "admin"
    educator = "educator"


class MessageRole(str, enum.Enum):
    user = "user"
    tutor = "tutor"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    avatar_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    role: Mapped[str] = mapped_column(String(32), default="user", nullable=False)
    subscription_plan: Mapped[str] = mapped_column(String(32), default="free", nullable=False)
    subscription_status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)
    subscription_current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    settings: Mapped[UserSettings] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    conversations: Mapped[list[Conversation]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    public_shares: Mapped[list["PublicConversation"]] = relationship(
        "PublicConversation",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    educator_classes: Mapped[list["Classroom"]] = relationship(
        "Classroom",
        back_populates="educator",
        cascade="all, delete-orphan",
        foreign_keys="Classroom.educator_id",
    )
    student_class_links: Mapped[list["ClassStudent"]] = relationship(
        "ClassStudent",
        back_populates="student",
        cascade="all, delete-orphan",
        foreign_keys="ClassStudent.student_id",
    )
    gamification: Mapped[GamificationProgress | None] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    pedagogy: Mapped["UserPedagogy | None"] = relationship(
        "UserPedagogy",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    user_skills: Mapped[list["UserSkill"]] = relationship(
        "UserSkill",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    created_topics: Mapped[list["Topic"]] = relationship(
        "Topic",
        back_populates="creator",
        foreign_keys="Topic.created_by",
    )
    topic_progress: Mapped[list["UserTopicProgress"]] = relationship(
        "UserTopicProgress",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class UserSettings(Base):
    __tablename__ = "user_settings"
    __table_args__ = (UniqueConstraint("user_id", name="uq_user_settings_user"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    tutor_mode: Mapped[str] = mapped_column(String(32), default="friendly", nullable=False)
    theme: Mapped[str | None] = mapped_column(String(16), nullable=True)
    notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    has_seen_onboarding: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    show_typing_indicator: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    russian_only: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # Локальная / кастомная LLM (OpenAI-совместимый /v1/chat/completions). Пусто = OpenRouter из .env.
    llm_base_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    llm_api_key: Mapped[str | None] = mapped_column(Text(), nullable=True)
    llm_model_name: Mapped[str | None] = mapped_column(String(256), nullable=True)

    user: Mapped[User] = relationship(back_populates="settings")


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(512), default="Новый диалог", nullable=False)
    session_key: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    assignment_id: Mapped[int | None] = mapped_column(
        ForeignKey("assignments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    last_updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user: Mapped[User] = relationship(back_populates="conversations")
    messages: Mapped[list[Message]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )
    public_share: Mapped["PublicConversation | None"] = relationship(
        "PublicConversation",
        back_populates="conversation",
        uselist=False,
        cascade="all, delete-orphan",
    )
    assignment: Mapped["Assignment | None"] = relationship("Assignment", back_populates="conversations")


class Classroom(Base):
    __tablename__ = "classes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    educator_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    educator: Mapped["User"] = relationship(
        "User",
        back_populates="educator_classes",
        foreign_keys=[educator_id],
    )
    students: Mapped[list["ClassStudent"]] = relationship(
        "ClassStudent",
        back_populates="classroom",
        cascade="all, delete-orphan",
    )
    assignments: Mapped[list["Assignment"]] = relationship(
        "Assignment",
        back_populates="classroom",
        cascade="all, delete-orphan",
    )


class ClassStudent(Base):
    __tablename__ = "class_students"

    class_id: Mapped[int] = mapped_column(
        ForeignKey("classes.id", ondelete="CASCADE"),
        primary_key=True,
    )
    student_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    classroom: Mapped["Classroom"] = relationship("Classroom", back_populates="students")
    student: Mapped["User"] = relationship(
        "User",
        back_populates="student_class_links",
        foreign_keys=[student_id],
    )


class Assignment(Base):
    __tablename__ = "assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    class_id: Mapped[int] = mapped_column(ForeignKey("classes.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    classroom: Mapped["Classroom"] = relationship("Classroom", back_populates="assignments")
    conversations: Mapped[list["Conversation"]] = relationship("Conversation", back_populates="assignment")


class PublicConversation(Base):
    """Публичная анонимная ссылка на диалог (одна активная запись на conversation)."""

    __tablename__ = "public_conversations"

    slug: Mapped[str] = mapped_column(String(16), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    views: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    user: Mapped["User"] = relationship(back_populates="public_shares")
    conversation: Mapped["Conversation"] = relationship(back_populates="public_share")


class Message(Base):
    __tablename__ = "messages"
    __table_args__ = (
        UniqueConstraint(
            "conversation_id",
            "client_message_id",
            name="uq_messages_conversation_client_message_id",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    client_message_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    fallacy_detected: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    conversation: Mapped[Conversation] = relationship(back_populates="messages")


class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(512), nullable=True)
    initial_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    tags: Mapped[list] = mapped_column(JSONType, default=list, nullable=False)
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_by: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    creator: Mapped["User"] = relationship("User", back_populates="created_topics", foreign_keys=[created_by])
    progress_rows: Mapped[list["UserTopicProgress"]] = relationship(
        "UserTopicProgress",
        back_populates="topic",
        cascade="all, delete-orphan",
    )


class UserTopicProgress(Base):
    __tablename__ = "user_topic_progress"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id", ondelete="CASCADE"), primary_key=True)
    completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_used: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="topic_progress")
    topic: Mapped["Topic"] = relationship("Topic", back_populates="progress_rows")


class Skill(Base):
    """Справочник навыков (общий для всех пользователей)."""

    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    skill_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    default_level: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class UserSkill(Base):
    __tablename__ = "user_skills"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    skill_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("skills.skill_id", ondelete="CASCADE"),
        primary_key=True,
    )
    level: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user: Mapped["User"] = relationship(back_populates="user_skills")
    skill: Mapped["Skill"] = relationship()


class UserPedagogy(Base):
    """Долговременное педагогическое состояние (между диалогами)."""

    __tablename__ = "user_pedagogy"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    current_difficulty: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    total_deep_responses: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_shallow_responses: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    fallacy_counts: Mapped[dict] = mapped_column(JSONType, nullable=False)
    last_active_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    logic_check_counter: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    user: Mapped["User"] = relationship(back_populates="pedagogy")


class GamificationProgress(Base):
    __tablename__ = "gamification_progress"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    wisdom_points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    achievements: Mapped[list] = mapped_column(JSONType, nullable=False)
    streak_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_daily_challenge_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    extra_state: Mapped[dict | None] = mapped_column(JSONType, nullable=True)

    user: Mapped[User] = relationship(back_populates="gamification")
