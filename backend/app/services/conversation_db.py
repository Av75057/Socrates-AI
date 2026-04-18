"""Сохранение сообщений и диалогов в БД."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Conversation, Message


def get_owned_conversation(db: Session, user_id: int, conversation_id: int) -> Conversation | None:
    c = db.get(Conversation, conversation_id)
    if c is None or c.user_id != user_id:
        return None
    return c


def create_conversation(db: Session, user_id: int, title: str | None, session_key: str) -> Conversation:
    now = datetime.now(timezone.utc)
    c = Conversation(
        user_id=user_id,
        title=(title or "Новый диалог")[:512],
        session_key=session_key,
        started_at=now,
        last_updated_at=now,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


def touch_conversation(db: Session, conv: Conversation) -> None:
    conv.last_updated_at = datetime.now(timezone.utc)
    db.commit()


def append_messages(
    db: Session,
    conversation_id: int,
    user_id: int,
    user_text: str,
    tutor_text: str,
    fallacy: dict[str, Any] | None,
) -> None:
    conv = get_owned_conversation(db, user_id, conversation_id)
    if conv is None:
        return
    db.add(
        Message(
            conversation_id=conv.id,
            role="user",
            content=user_text,
            fallacy_detected=fallacy,
        )
    )
    db.add(
        Message(
            conversation_id=conv.id,
            role="tutor",
            content=tutor_text,
            fallacy_detected=None,
        )
    )
    touch_conversation(db, conv)


def conversation_message_count(db: Session, conversation_id: int) -> int:
    return db.scalar(
        select(func.count()).select_from(Message).where(Message.conversation_id == conversation_id)
    ) or 0


def fallacy_summary_for_user(db: Session, user_id: int, limit: int = 20) -> list[dict[str, Any]]:
    rows = db.execute(
        select(Message.fallacy_detected)
        .join(Conversation, Message.conversation_id == Conversation.id)
        .where(
            Conversation.user_id == user_id,
            Message.role == "user",
            Message.fallacy_detected.isnot(None),
        )
    ).scalars()
    counts: dict[str, int] = {}
    for raw in rows:
        if not isinstance(raw, dict):
            continue
        ft = str(raw.get("fallacy_type") or "")
        if ft and ft != "none":
            counts[ft] = counts.get(ft, 0) + 1
    ranked = sorted(counts.items(), key=lambda x: -x[1])[:limit]
    return [{"fallacy_type": k, "count": v} for k, v in ranked]
