from __future__ import annotations

import asyncio
import json
import logging
import time
from collections.abc import AsyncGenerator
from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from app.api.deps_auth import get_current_user_optional
from app.db.models import User
from app.deps import redis_dep
from app.dto.chat_schema import ChatRequest, ChatResponse
from app.logging_context import log_context
from app.logging_setup import log_event
from app.services.chat_orchestrator import ChatOrchestrator

router = APIRouter()
log = logging.getLogger(__name__)
orchestrator = ChatOrchestrator()


def _sse_event(event: str, data: Any) -> str:
    payload = data if isinstance(data, str) else json.dumps(data, ensure_ascii=False)
    return f"event: {event}\ndata: {payload}\n\n"


@router.post("/chat", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    request: Request,
    r=Depends(redis_dep),
    db_user: User | None = Depends(get_current_user_optional),
):
    correlation_id = request.state.correlation_id
    with log_context(
        correlation_id=correlation_id,
        user_id=str(db_user.id) if db_user else None,
        session_id=body.session_id,
        conversation_id=body.conversation_id,
    ):
        result = await orchestrator.process_message(body, r, db_user, correlation_id)
        return result.response


@router.post("/chat/message/stream")
async def chat_message_stream(
    body: ChatRequest,
    request: Request,
    r=Depends(redis_dep),
    db_user: User | None = Depends(get_current_user_optional),
):
    correlation_id = request.state.correlation_id
    context = await orchestrator.prepare_message(body, r, db_user, correlation_id)
    if context.duplicate_response is not None:

        async def _duplicate_stream() -> AsyncGenerator[str, None]:
            yield _sse_event(
                "meta",
                {
                    "conversation_id": context.duplicate_response.conversation_id,
                    "session_key": context.duplicate_response.session_key,
                },
            )
            yield _sse_event("done", context.duplicate_response.model_dump())

        return StreamingResponse(_duplicate_stream(), media_type="text/event-stream")

    controller = orchestrator.controller_factory(context.router)
    context.analysis = await orchestrator.answer_analyzer.analyze(context)
    orchestrator.advance_state_for_turn(context)
    plan = orchestrator.instruction_builder.build_prompt(context, controller)

    async def _event_stream() -> AsyncGenerator[str, None]:
        parts: list[str] = []
        started = False
        started_at = time.perf_counter()
        with log_context(
            correlation_id=correlation_id,
            user_id=context.prepared_turn.user_id,
            session_id=body.session_id,
            conversation_id=context.active_conversation_id,
            phase=context.current_phase.value,
        ):
            try:
                yield _sse_event(
                    "meta",
                    {
                        "conversation_id": context.active_conversation_id,
                        "session_key": body.session_id,
                    },
                )
                if plan.immediate_reply is not None:
                    if await request.is_disconnected():
                        raise asyncio.CancelledError()
                    parts.append(plan.immediate_reply)
                    started = True
                    yield _sse_event("chunk", plan.immediate_reply)
                else:
                    async for chunk in context.router.generate_stream(plan.prompt or "", plan.user_line, plan.mode):
                        if await request.is_disconnected():
                            raise asyncio.CancelledError()
                        if not chunk:
                            continue
                        started = True
                        parts.append(chunk)
                        yield _sse_event("chunk", chunk)
                context.latency_ms = int((time.perf_counter() - started_at) * 1000)
                raw_reply = "".join(parts).strip() or "…"
                result = await orchestrator.finalize_stream_reply(context, controller, plan, raw_reply)
                yield _sse_event("done", result.response.model_dump())
            except asyncio.CancelledError:
                log_event(
                    log,
                    logging.INFO,
                    "Chat stream cancelled",
                    session_id=body.session_id,
                    conversation_id=context.active_conversation_id,
                    phase=context.current_phase.value,
                )
                raise
            except Exception as exc:
                log.exception("chat stream failed")
                if not started:
                    yield _sse_event("error", {"message": str(exc)})

    return StreamingResponse(
        _event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
