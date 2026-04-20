from __future__ import annotations

import json
import logging
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps_auth import get_current_user
from app.db.models import Conversation, Message, User, UserSettings
from app.db.session import get_db
from app.deps import redis_dep
from app.services.memory_store import load_memory
from app.services.conversation_db import (
    append_tutor_opening,
    conversation_message_count,
    create_conversation,
    delete_user_message_and_following,
    display_title_for_conversation,
    fallacy_summary_for_user,
    update_user_message_content,
)
from app.services.conversation_opening import generate_conversation_opening_message
from app.services.db_gamification import ensure_gamification_row, gamification_row_to_public
from app.services.learning_service import (
    get_recommendation,
    get_user_pedagogy_public,
    get_user_skills_summary,
    reset_user_learning,
)

router = APIRouter(prefix="/users", tags=["users"])
log = logging.getLogger(__name__)


def _normalize_fallacy_detected(raw: Any) -> dict[str, Any] | None:
    """SQLite/драйверы могут отдать JSON строкой; Pydantic ждёт dict | None."""
    if raw is None:
        return None
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str) and raw.strip():
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            return None
    return None


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
    has_seen_onboarding: bool
    show_typing_indicator: bool


class SettingsUpdate(BaseModel):
    tutor_mode: str | None = None
    theme: str | None = None
    notifications_enabled: bool | None = None
    has_seen_onboarding: bool | None = None
    show_typing_indicator: bool | None = None


class MessageContentUpdate(BaseModel):
    content: str = Field(..., min_length=1, max_length=65535)


class ConversationCreate(BaseModel):
    title: str | None = Field(None, max_length=512)


class ConversationSummary(BaseModel):
    id: int
    title: str
    started_at: str
    last_updated_at: str
    message_count: int
    session_key: str
    opening_message: str | None = None


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


@router.get("/me/memory-profile")
async def get_memory_profile_me(
    user: User = Depends(get_current_user),
    r=Depends(redis_dep),
):
    """
    Долговременная память тьютора из Redis (тот же ключ, что и в /chat для аккаунта).
    Нужна UI при смене диалога без нового сообщения — иначе панель «Память тьютора» остаётся пустой/устаревшей.
    """
    memory = await load_memory(r, str(user.id))
    ut = memory.user_type if memory.user_type in ("lazy", "anxious", "thinker") else "lazy"
    out = memory.to_dict()
    out["user_type"] = ut
    return out


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
        s = UserSettings(
            user_id=user.id,
            tutor_mode="friendly",
            theme="dark",
            notifications_enabled=True,
            has_seen_onboarding=False,
            show_typing_indicator=True,
        )
        db.add(s)
        db.commit()
        db.refresh(s)
    return SettingsOut(
        tutor_mode=s.tutor_mode,
        theme=s.theme,
        notifications_enabled=s.notifications_enabled,
        has_seen_onboarding=bool(s.has_seen_onboarding),
        show_typing_indicator=bool(s.show_typing_indicator),
    )


@router.put("/me/settings", response_model=SettingsOut)
def update_settings_me(
    body: SettingsUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    s = _settings_for_user(db, user.id)
    if s is None:
        s = UserSettings(
            user_id=user.id,
            tutor_mode="friendly",
            theme="dark",
            notifications_enabled=True,
            has_seen_onboarding=False,
            show_typing_indicator=True,
        )
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
    if body.has_seen_onboarding is not None:
        s.has_seen_onboarding = body.has_seen_onboarding
    if body.show_typing_indicator is not None:
        s.show_typing_indicator = body.show_typing_indicator
    db.commit()
    db.refresh(s)
    return SettingsOut(
        tutor_mode=s.tutor_mode,
        theme=s.theme,
        notifications_enabled=s.notifications_enabled,
        has_seen_onboarding=bool(s.has_seen_onboarding),
        show_typing_indicator=bool(s.show_typing_indicator),
    )


@router.post("/me/conversations", response_model=ConversationSummary)
async def create_conversation_me(
    body: ConversationCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session_key = str(uuid.uuid4())
    c = create_conversation(db, user.id, body.title, session_key)
    opening: str | None = None
    try:
        raw = await generate_conversation_opening_message(user.id, c.title)
        if raw:
            append_tutor_opening(db, c.id, user.id, raw)
            opening = raw
    except Exception:
        log.exception("conversation opening failed user_id=%s conv_id=%s", user.id, c.id)
    db.refresh(c)
    mc = conversation_message_count(db, c.id)
    return ConversationSummary(
        id=c.id,
        title=c.title,
        started_at=c.started_at.isoformat(),
        last_updated_at=c.last_updated_at.isoformat(),
        message_count=mc,
        session_key=c.session_key,
        opening_message=opening,
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
                title=display_title_for_conversation(db, c),
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
        title=display_title_for_conversation(db, c),
        started_at=c.started_at.isoformat(),
        last_updated_at=c.last_updated_at.isoformat(),
        session_key=c.session_key,
        messages=[
            MessageOut(
                id=m.id,
                role=m.role,
                content=m.content,
                fallacy_detected=_normalize_fallacy_detected(m.fallacy_detected),
                created_at=m.created_at.isoformat(),
            )
            for m in msgs
        ],
    )


@router.put("/me/messages/{message_id}", response_model=MessageOut)
def update_message_me(
    message_id: int,
    body: MessageContentUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ok = update_user_message_content(db, user.id, message_id, body.content)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found or not editable")
    m = db.get(Message, message_id)
    if m is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    return MessageOut(
        id=m.id,
        role=m.role,
        content=m.content,
        fallacy_detected=_normalize_fallacy_detected(m.fallacy_detected),
        created_at=m.created_at.isoformat(),
    )


@router.delete("/me/messages/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_message_me(
    message_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    n = delete_user_message_and_following(db, user.id, message_id)
    if n == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found or not deletable")
    return None


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


def _dialog_statistics(db: Session, user_id: int) -> dict[str, Any]:
    n_conv = db.scalar(select(func.count()).select_from(Conversation).where(Conversation.user_id == user_id)) or 0
    n_msg = (
        db.scalar(
            select(func.count())
            .select_from(Message)
            .join(Conversation, Message.conversation_id == Conversation.id)
            .where(Conversation.user_id == user_id)
        )
        or 0
    )
    n_user_msgs = (
        db.scalar(
            select(func.count())
            .select_from(Message)
            .join(Conversation, Message.conversation_id == Conversation.id)
            .where(Conversation.user_id == user_id, Message.role == "user")
        )
        or 0
    )
    avg_len = 0.0
    if n_user_msgs:
        total = db.scalar(
            select(func.sum(func.length(Message.content)))
            .join(Conversation, Message.conversation_id == Conversation.id)
            .where(Conversation.user_id == user_id, Message.role == "user")
        )
        if total:
            avg_len = round(float(total) / n_user_msgs, 2)
    return {
        "conversations_total": n_conv,
        "messages_total": n_msg,
        "user_messages_total": n_user_msgs,
        "avg_user_message_length": avg_len,
        "common_fallacies": fallacy_summary_for_user(db, user_id, limit=10),
    }


@router.get("/me/statistics")
def get_statistics_me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _dialog_statistics(db, user.id)


@router.get("/me/skills")
def get_skills_me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return get_user_skills_summary(db, user.id)


@router.get("/me/pedagogy")
def get_pedagogy_me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return get_user_pedagogy_public(db, user.id)


@router.get("/me/progress")
def get_progress_me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return {
        "skills": get_user_skills_summary(db, user.id),
        "pedagogy": get_user_pedagogy_public(db, user.id),
        "dialog_statistics": _dialog_statistics(db, user.id),
    }


@router.get("/me/recommendation")
def get_recommendation_me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return get_recommendation(db, user.id)


@router.post("/me/reset_progress", status_code=status.HTTP_204_NO_CONTENT)
def reset_progress_me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    reset_user_learning(db, user.id)
    return None
