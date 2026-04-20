"""Хранение прогресса геймификации в Redis (или in-memory)."""

from __future__ import annotations

from typing import Any, Protocol

from app.models.gamification import UserProgressState


class _AsyncKV(Protocol):
    async def get(self, key: str) -> str | None: ...
    async def set(self, key: str, value: str) -> Any: ...


def progress_redis_key(session_id: str, account_user_id: int | None) -> str:
    """Гость — по session_id; авторизованный — один ключ на аккаунт (прогресс не теряется между чатами)."""
    if account_user_id is not None:
        return f"gamification:user:{account_user_id}"
    return f"gamification:{session_id.strip()}"


def _display_user_id(session_id: str, account_user_id: int | None) -> str:
    if account_user_id is not None:
        return str(account_user_id)
    return session_id.strip()


async def load_progress(
    client: _AsyncKV,
    session_id: str,
    account_user_id: int | None = None,
) -> tuple[UserProgressState, bool]:
    """
    Возвращает (состояние, redis_hit).
    Если ключа в Redis нет, состояние — начальное с корректным user_id для сида вызовов/паблика API.
    """
    sid = session_id.strip()
    if account_user_id is None and not sid:
        return UserProgressState(user_id=""), False
    key = progress_redis_key(session_id, account_user_id)
    display_id = _display_user_id(session_id, account_user_id)
    raw = await client.get(key)
    if not raw:
        return UserProgressState(user_id=display_id), False
    parsed = UserProgressState.from_json(raw)
    if parsed is None:
        # Битый JSON — как промах, чтобы для аккаунта подтянуть БД и не показывать нули
        return UserProgressState(user_id=display_id), False
    if parsed.user_id != display_id:
        parsed.user_id = display_id
    return parsed, True


async def save_progress(
    client: _AsyncKV,
    session_id: str,
    state: UserProgressState,
    account_user_id: int | None = None,
) -> None:
    sid = session_id.strip()
    if account_user_id is None and not sid:
        return
    key = progress_redis_key(session_id, account_user_id)
    state.user_id = _display_user_id(session_id, account_user_id)
    await client.set(key, state.to_json())
