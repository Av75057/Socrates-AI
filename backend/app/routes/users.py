from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps_auth import get_current_user
from app.db.models import Conversation, Message, User, UserSettings
from app.db.session import get_db
from app.services.conversation_db import conversation_message_count, fallacy_summary_for_user
from app.services.db_gamification import ensure_gamification_row, gamification_row_to_public

router = APIRouter(prefix="/users", tags=["users"])


class ProfileOut(BaseModel):
    id: int
    email: str
    full_name: str | None
    role: str
    is_active: bool


class ProfileUpdate(BaseModel):
    full_name: str | None = Field(None, max_length=255)


class SettingsOut(BaseModel):
    tutor_mode: str
    theme: str | None
    notifications_enabled: bool


class SettingsUpdate(BaseModel):
    tutor_mode: str | None = None
    theme: str | None = None
    notifications_enabled: bool | None = None


class ConversationCreate(BaseModel):
    title: str | None = Field(None, max_length=512)


class ConversationSummary(BaseModel):
    id: int
    title: str
    started_at: str
    last_updated_at: str
    message_count: int
    session_key: str


class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    fallacy_detected: dict[str, Any] | None
    created_at: str


class ConversationDetail(BaseModel):
    id: int
    title: str
    started_at: str
    last_updated_at: str
    session_key: str
    messages: list[MessageOut]


@router.get("/me", response_model=ProfileOut)
def get_me(user: User = Depends(get_current_user)):
    return ProfileOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
    )


@router.put("/me", response_model=ProfileOut)
def update_me(body: ProfileUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if body.full_name is not None:
        user.full_name = body.full_name
    db.commit()
    db.refresh(user)
    return ProfileOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
    )


def _settings_for_user(db: Session, user_id: int) -> UserSettings | None:
    return db.execute(select(UserSettings).where(UserSettings.user_id == user_id)).scalar_one_or_none()


@router.get("/me/settings", response_model=SettingsOut)
def get_settings_me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    s = _settings_for_user(db, user.id)
    if s is None:
        s = UserSettings(user_id=user.id, tutor_mode="friendly", theme="dark", notifications_enabled=True)
        db.add(s)
        db.commit()
        db.refresh(s)
    return SettingsOut(
        tutor_mode=s.tutor_mode,
        theme=s.theme,
        notifications_enabled=s.notifications_enabled,
    )


@router.put("/me/settings", response_model=SettingsOut)
def update_settings_me(
    body: SettingsUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    s = _settings_for_user(db, user.id)
    if s is None:
        s = UserSettings(user_id=user.id, tutor_mode="friendly", theme="dark", notifications_enabled=True)
        db.add(s)
        db.flush()
    if body.tutor_mode is not None:
        if body.tutor_mode not in ("strict", "friendly", "provocateur"):
            raise HTTPException(status_code=400, detail="Invalid tutor_mode")
        s.tutor_mode = body.tutor_mode
    if body.theme is not None:
        if body.theme not in ("light", "dark"):
            raise HTTPException(status_code=400, detail="Invalid theme")
        s.theme = body.theme
    if body.notifications_enabled is not None:
        s.notifications_enabled = body.notifications_enabled
    db.commit()
    db.refresh(s)
    return SettingsOut(
        tutor_mode=s.tutor_mode,
        theme=s.theme,
        notifications_enabled=s.notifications_enabled,
    )


@router.post("/me/conversations", response_model=ConversationSummary)
def create_conversation_me(
    body: ConversationCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    import uuid

    session_key = str(uuid.uuid4())
    from app.services.conversation_db import create_conversation

    c = create_conversation(db, user.id, body.title, session_key)
    return ConversationSummary(
        id=c.id,
        title=c.title,
        started_at=c.started_at.isoformat(),
        last_updated_at=c.last_updated_at.isoformat(),
        message_count=0,
        session_key=c.session_key,
    )


@router.get("/me/conversations", response_model=list[ConversationSummary])
def list_conversations_me(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    rows = (
        db.execute(
            select(Conversation)
            .where(Conversation.user_id == user.id)
            .order_by(Conversation.last_updated_at.desc())
            .offset(offset)
            .limit(limit)
        )
        .scalars()
        .all()
    )
    out: list[ConversationSummary] = []
    for c in rows:
        out.append(
            ConversationSummary(
                id=c.id,
                title=c.title,
                started_at=c.started_at.isoformat(),
                last_updated_at=c.last_updated_at.isoformat(),
                message_count=conversation_message_count(db, c.id),
                session_key=c.session_key,
            )
        )
    return out


@router.get("/me/conversations/{conversation_id}", response_model=ConversationDetail)
def get_conversation_me(
    conversation_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    c = db.get(Conversation, conversation_id)
    if c is None or c.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    msgs = (
        db.execute(
            select(Message)
            .where(Message.conversation_id == c.id)
            .order_by(Message.created_at.asc())
        )
        .scalars()
        .all()
    )
    return ConversationDetail(
        id=c.id,
        title=c.title,
        started_at=c.started_at.isoformat(),
        last_updated_at=c.last_updated_at.isoformat(),
        session_key=c.session_key,
        messages=[
            MessageOut(
                id=m.id,
                role=m.role,
                content=m.content,
                fallacy_detected=m.fallacy_detected,
                created_at=m.created_at.isoformat(),
            )
            for m in msgs
        ],
    )


@router.delete("/me/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation_me(
    conversation_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    c = db.get(Conversation, conversation_id)
    if c is None or c.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    db.delete(c)
    db.commit()
    return None


@router.get("/me/gamification")
def get_gamification_me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    row = ensure_gamification_row(db, user.id)
    return gamification_row_to_public(row)


@router.get("/me/statistics")
def get_statistics_me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    n_conv = db.scalar(select(func.count()).select_from(Conversation).where(Conversation.user_id == user.id)) or 0
    n_msg = (
        db.scalar(
            select(func.count())
            .select_from(Message)
            .join(Conversation, Message.conversation_id == Conversation.id)
            .where(Conversation.user_id == user.id)
        )
        or 0
    )
    n_user_msgs = (
        db.scalar(
            select(func.count())
            .select_from(Message)
            .join(Conversation, Message.conversation_id == Conversation.id)
            .where(Conversation.user_id == user.id, Message.role == "user")
        )
        or 0
    )
    avg_len = 0.0
    if n_user_msgs:
        total = db.scalar(
            select(func.sum(func.length(Message.content)))
            .join(Conversation, Message.conversation_id == Conversation.id)
            .where(Conversation.user_id == user.id, Message.role == "user")
        )
        if total:
            avg_len = round(float(total) / n_user_msgs, 2)
    return {
        "conversations_total": n_conv,
        "messages_total": n_msg,
        "user_messages_total": n_user_msgs,
        "avg_user_message_length": avg_len,
        "common_fallacies": fallacy_summary_for_user(db, user.id, limit=10),
    }
