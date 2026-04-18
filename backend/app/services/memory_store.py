"""Загрузка / сохранение UserMemory в Redis."""

from __future__ import annotations

import json
from typing import Any, Protocol

from app.models.user_memory import UserMemory


class _AsyncKV(Protocol):
    async def get(self, key: str) -> str | None: ...
    async def set(self, key: str, value: str) -> Any: ...


def _memory_key(user_id: str) -> str:
    return f"socrates:memory:{user_id}"


async def load_memory(client: _AsyncKV, user_id: str) -> UserMemory:
    if not user_id.strip():
        return UserMemory()
    raw = await client.get(_memory_key(user_id.strip()))
    if not raw:
        return UserMemory()
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return UserMemory.from_dict(data)
    except (json.JSONDecodeError, TypeError, ValueError):
        pass
    return UserMemory()


async def save_memory(client: _AsyncKV, user_id: str, memory: UserMemory) -> None:
    if not user_id.strip():
        return
    await client.set(_memory_key(user_id.strip()), json.dumps(memory.to_dict(), ensure_ascii=False))
