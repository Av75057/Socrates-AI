"""Redis / memory-хранилище педагогического состояния."""

from __future__ import annotations

from typing import Any, Protocol

from app.models.pedagogy import TutorMode, UserPedagogyState


class _AsyncKV(Protocol):
    async def get(self, key: str) -> str | None: ...
    async def set(self, key: str, value: str) -> Any: ...


def _pkey(session_id: str) -> str:
    return f"pedagogy:{session_id.strip()}"


async def load_pedagogy(client: _AsyncKV, session_id: str) -> UserPedagogyState:
    sid = session_id.strip()
    if not sid:
        return UserPedagogyState()
    raw = await client.get(_pkey(sid))
    if not raw:
        return UserPedagogyState(session_id=sid, mode=TutorMode.FRIENDLY)
    parsed = UserPedagogyState.from_json(raw)
    if parsed is None:
        return UserPedagogyState(session_id=sid, mode=TutorMode.FRIENDLY)
    parsed.session_id = sid
    return parsed


async def save_pedagogy(client: _AsyncKV, session_id: str, state: UserPedagogyState) -> None:
    sid = session_id.strip()
    if not sid:
        return
    state.session_id = sid
    await client.set(_pkey(sid), state.to_json())
