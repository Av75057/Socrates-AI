"""Хранение прогресса геймификации в Redis (или in-memory)."""

from __future__ import annotations

from typing import Any, Protocol

from app.models.gamification import UserProgressState


class _AsyncKV(Protocol):
    async def get(self, key: str) -> str | None: ...
    async def set(self, key: str, value: str) -> Any: ...


def _gkey(session_id: str) -> str:
    return f"gamification:{session_id.strip()}"


async def load_progress(client: _AsyncKV, session_id: str) -> UserProgressState:
    sid = session_id.strip()
    if not sid:
        return UserProgressState(user_id="")
    raw = await client.get(_gkey(sid))
    if not raw:
        return UserProgressState(user_id=sid)
    parsed = UserProgressState.from_json(raw)
    if parsed is None:
        return UserProgressState(user_id=sid)
    if parsed.user_id != sid:
        parsed.user_id = sid
    return parsed


async def save_progress(client: _AsyncKV, session_id: str, state: UserProgressState) -> None:
    sid = session_id.strip()
    if not sid:
        return
    state.user_id = sid
    await client.set(_gkey(sid), state.to_json())
