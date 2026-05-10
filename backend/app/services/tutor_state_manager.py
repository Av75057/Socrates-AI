from __future__ import annotations

from typing import Any

from starlette.concurrency import run_in_threadpool

from app.db.models import Conversation
from app.db.session import SessionLocal

DEFAULT_TUTOR_STATE: dict[str, Any] = {
    "level": 2,
    "mode": "friendly",
    "step": 0,
    "stuck": False,
    "last_fallacy": None,
    "topic": "general",
    "attempted_concepts": [],
}


def _merged_state(raw: dict[str, Any] | None) -> dict[str, Any]:
    state = dict(DEFAULT_TUTOR_STATE)
    if isinstance(raw, dict):
        state.update(raw)
    attempted = state.get("attempted_concepts")
    state["attempted_concepts"] = list(attempted) if isinstance(attempted, list) else []
    return state


async def get_tutor_state(conv_id: int) -> dict[str, Any]:
    def _load() -> dict[str, Any]:
        with SessionLocal() as db:
            conv = db.get(Conversation, conv_id)
            if conv is None:
                return dict(DEFAULT_TUTOR_STATE)
            return _merged_state(conv.tutor_state if isinstance(conv.tutor_state, dict) else None)

    return await run_in_threadpool(_load)


async def update_tutor_state(conv_id: int, updates: dict[str, Any]) -> dict[str, Any]:
    def _update() -> dict[str, Any]:
        with SessionLocal() as db:
            conv = db.get(Conversation, conv_id)
            if conv is None:
                return dict(DEFAULT_TUTOR_STATE)
            merged = _merged_state(conv.tutor_state if isinstance(conv.tutor_state, dict) else None)
            merged.update(updates or {})
            attempted = merged.get("attempted_concepts")
            merged["attempted_concepts"] = list(attempted) if isinstance(attempted, list) else []
            conv.tutor_state = merged
            db.add(conv)
            db.commit()
            return merged

    return await run_in_threadpool(_update)
