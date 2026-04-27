from __future__ import annotations

from typing import Any, Protocol

from app.models.meta_training import MetaTrainingSessionState


class _KV(Protocol):
    async def get(self, key: str) -> str | None: ...
    async def set(self, key: str, value: str) -> Any: ...


def _key(session_id: str) -> str:
    return f"socrates:meta-training:{session_id.strip()}"


async def load_meta_training_state(client: _KV, session_id: str) -> MetaTrainingSessionState | None:
    raw = await client.get(_key(session_id))
    if not raw:
        return None
    return MetaTrainingSessionState.from_json(raw)


async def save_meta_training_state(client: _KV, state: MetaTrainingSessionState) -> None:
    await client.set(_key(state.session_id), state.to_json())
