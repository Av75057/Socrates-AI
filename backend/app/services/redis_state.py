"""Redis persistence for TutorState; optional in-memory store for dev."""

from __future__ import annotations

import json
from typing import Any, Protocol

import redis.asyncio as redis

from app.models.state import TutorState


class _KV(Protocol):
    async def get(self, key: str) -> str | None: ...
    async def set(self, key: str, value: str) -> Any: ...


def _key(session_id: str) -> str:
    return f"socrates:session:{session_id}"


class _MemoryKV:
    """Minimal async key-value for local dev when Redis is unavailable."""

    def __init__(self) -> None:
        self._data: dict[str, str] = {}

    async def get(self, key: str) -> str | None:
        return self._data.get(key)

    async def set(self, key: str, value: str) -> str:
        self._data[key] = value
        return "OK"


async def load_state(client: _KV, session_id: str) -> TutorState:
    raw = await client.get(_key(session_id))
    if not raw:
        return TutorState()
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return TutorState.from_dict(data)
    except (json.JSONDecodeError, TypeError, ValueError):
        pass
    return TutorState()


async def save_state(client: _KV, session_id: str, state: TutorState) -> None:
    await client.set(_key(session_id), json.dumps(state.to_dict(), ensure_ascii=False))


async def get_redis(url: str) -> _KV:
    if url.strip().lower() == "memory":
        return _MemoryKV()
    return redis.from_url(url, decode_responses=True)
