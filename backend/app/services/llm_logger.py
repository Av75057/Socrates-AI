from __future__ import annotations

import re
from typing import Any

from starlette.concurrency import run_in_threadpool

from app.db.models import LLMLog
from app.db.session import SessionLocal

_TOKEN_RE = re.compile(r"[^\s]+", re.UNICODE)


def estimate_response_tokens(text: str) -> int:
    return len(_TOKEN_RE.findall(str(text or "")))


async def save_llm_log(
    *,
    conversation_id: int | None,
    user_id: int | None,
    system_prompt: str,
    user_messages: list[dict[str, Any]] | dict[str, Any],
    model_params: dict[str, Any],
    raw_response: str,
    response_tokens: int | None = None,
    latency_ms: int = 0,
) -> None:
    tokens = int(response_tokens if response_tokens is not None else estimate_response_tokens(raw_response))

    def _save() -> None:
        with SessionLocal() as db:
            row = LLMLog(
                conversation_id=conversation_id,
                user_id=user_id,
                system_prompt=system_prompt or "",
                user_messages=user_messages or [],
                model_params=model_params or {},
                raw_response=raw_response or "",
                response_tokens=tokens,
                latency_ms=max(0, int(latency_ms or 0)),
            )
            db.add(row)
            db.commit()

    await run_in_threadpool(_save)
