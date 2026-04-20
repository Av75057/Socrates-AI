"""Сохранение сообщений и диалогов в БД."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.db.models import Conversation, Message
from app.models.state import TutorState

# Заголовки «из коробки» — в истории заменяем на первый вопрос ученика.
_DEFAULT_CONVERSATION_TITLES = frozenset(
    {
        "новый диалог",
        "новая тема",
    }
)


def _is_default_conversation_title(title: str | None) -> bool:
    t = (title or "").strip().lower()
    if not t:
        return True
    return t in _DEFAULT_CONVERSATION_TITLES


def _is_placeholder_user_line_for_title(text: str) -> bool:
    """Подсказка/сдача и пустые строки — не использовать как название диалога."""
    s = (text or "").strip()
    if not s:
        return True
    if s.startswith("("):
        return True
    return False


def display_title_for_conversation(db: Session, conv: Conversation) -> str:
    """Для UI и истории: при шаблонном title показать первый вопрос ученика (если уже есть в БД)."""
    if not _is_default_conversation_title(conv.title):
        return conv.title
    first = db.execute(
        select(Message.content)
        .where(Message.conversation_id == conv.id, Message.role == "user")
        .order_by(Message.created_at.asc())
        .limit(1)
    ).scalar_one_or_none()
    if first is None or _is_placeholder_user_line_for_title(first):
        return conv.title
    t = first.strip()
    return t[:512] if len(t) > 512 else t


def _redis_history_is_valid(history: list[Any]) -> bool:
    if not history:
        return True
    for h in history:
        if not isinstance(h, dict):
            return False
        if h.get("role") not in ("user", "assistant"):
            return False
    return True


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


def hydrate_state_history_from_conversation_if_empty(
    db: Session,
    user_id: int,
    conversation_id: int,
    state: TutorState,
    *,
    max_messages: int = 40,
) -> None:
    """Если Redis-история пуста — подтянуть сообщения из БД (в т.ч. первый вопрос тьютора)."""
    if state.history and not _redis_history_is_valid(state.history):
        state.history = []
    if state.history:
        return
    conv = get_owned_conversation(db, user_id, conversation_id)
    if conv is None:
        return
    msgs = (
        db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .limit(max_messages)
        )
        .scalars()
        .all()
    )
    for m in msgs:
        role = "user" if m.role == "user" else "assistant"
        state.history.append({"role": role, "content": m.content})
    if conv.title and not (state.topic or "").strip():
        state.topic = conv.title.strip()


def append_tutor_opening(db: Session, conversation_id: int, user_id: int, tutor_text: str) -> None:
    """Одно сообщение тьютора в начале диалога (без сообщения пользователя)."""
    conv = get_owned_conversation(db, user_id, conversation_id)
    if conv is None or not (tutor_text or "").strip():
        return
    db.add(
        Message(
            conversation_id=conv.id,
            role="tutor",
            content=tutor_text.strip(),
            fallacy_detected=None,
        )
    )
    touch_conversation(db, conv)


def append_messages(
    db: Session,
    conversation_id: int,
    user_id: int,
    user_text: str,
    tutor_text: str,
    fallacy: dict[str, Any] | None,
) -> tuple[int, int] | None:
    conv = get_owned_conversation(db, user_id, conversation_id)
    if conv is None:
        return None
    u_row = Message(
        conversation_id=conv.id,
        role="user",
        content=user_text,
        fallacy_detected=fallacy,
    )
    t_row = Message(
        conversation_id=conv.id,
        role="tutor",
        content=tutor_text,
        fallacy_detected=None,
    )
    db.add(u_row)
    db.add(t_row)
    db.flush()
    uid, tid = u_row.id, t_row.id
    if not _is_placeholder_user_line_for_title(user_text) and _is_default_conversation_title(conv.title):
        conv.title = user_text.strip()[:512]
    touch_conversation(db, conv)
    return (uid, tid)


def update_user_message_content(
    db: Session,
    user_id: int,
    message_id: int,
    new_content: str,
) -> bool:
    """Обновить текст сообщения пользователя; владелец диалога — user_id."""
    msg = db.get(Message, message_id)
    if msg is None or msg.role != "user":
        return False
    conv = get_owned_conversation(db, user_id, msg.conversation_id)
    if conv is None:
        return False
    msg.content = (new_content or "")[:65535]
    touch_conversation(db, conv)
    return True


def delete_user_message_and_following(db: Session, user_id: int, message_id: int) -> int:
    """
    Удалить сообщение пользователя и все последующие в диалоге (по id).
    Возвращает число удалённых строк.
    """
    msg = db.get(Message, message_id)
    if msg is None or msg.role != "user":
        return 0
    conv = get_owned_conversation(db, user_id, msg.conversation_id)
    if conv is None:
        return 0
    res = db.execute(
        delete(Message).where(
            Message.conversation_id == conv.id,
            Message.id >= message_id,
        )
    )
    n = int(res.rowcount or 0)
    touch_conversation(db, conv)
    return n


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
