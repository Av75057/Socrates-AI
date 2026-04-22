from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from typing import Any, AsyncGenerator, Literal

from sqlalchemy import select
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from app.api.deps_auth import get_current_user_optional
from app.db.models import Assignment, ClassStudent, User
from app.config import get_settings
from app.db.session import SessionLocal
from app.deps import redis_dep
from app.models.pedagogy import PedagogyTurnContext, TutorMode
from app.services.cheat_detector import is_cheating
from app.services.difficulty_adjuster import apply_after_user_turn, apply_hint_penalty
from app.services.fallacy_detector import analyze_response
from app.services.pedagogy_heuristics import build_fallacy_instruction
from app.services.memory_manager import update_memory_after_turn
from app.services.memory_store import load_memory, save_memory
from app.services.model_router import ModelRouter
from app.services.pedagogy_store import load_pedagogy, save_pedagogy
from app.services.prompt_builder import _history_to_text
from app.services.redis_state import load_state, save_state
from app.services.skill_tree_manager import (
    align_tree_hint_with_session_topic,
    build_skill_tree_payload,
    canonical_subject_topic,
    resolve_track_hint,
)
from app.services.tutor_controller import TutorController
from app.services.tutor_prompt import is_tutor_answering_for_student
from app.services.conversation_db import (
    append_messages,
    find_duplicate_turn,
    get_owned_conversation,
    get_or_create_conversation_by_session_key,
    hydrate_state_history_from_conversation_if_empty,
)
from app.services.learning_service import (
    build_persistent_profile_for_prompt,
    hydrate_session_pedagogy_from_db,
    update_user_learning_progress_sync,
)
from app.services.user_settings_db import build_model_router_for_user, get_russian_only, get_tutor_mode

router = APIRouter()
log = logging.getLogger(__name__)
_SAFE_TUTOR_FALLBACK = "Хорошо. А как бы ты ответил сам?"


@dataclass
class PreparedChatTurn:
    body: "ChatRequest"
    redis_client: Any
    db_user: User | None
    msg_stripped: str
    idle_turn: bool
    active_conversation_id: int | None
    state: Any
    memory: Any
    mid: str
    prev_skill: dict[str, str]
    pedagogy_state: Any
    persistent_profile: str
    russian_only: bool
    cheat: bool
    router: ModelRouter
    analysis: dict[str, Any] | None


def _pedagogy_mode_str(mode: Any) -> str:
    """UserPedagogyState.mode — обычно TutorMode; из Redis теоретически может быть str."""
    if mode is None:
        return "friendly"
    if hasattr(mode, "value"):
        return str(mode.value)
    s = str(mode).strip().lower()
    return s if s in ("strict", "friendly", "provocateur") else "friendly"


def _last_assistant_question(history: list[dict[str, Any]]) -> str:
    for h in reversed(history):
        if not isinstance(h, dict):
            continue
        if h.get("role") == "assistant":
            return str(h.get("content") or "").strip()
    return ""


class ChatRequest(BaseModel):
    message: str = ""
    session_id: str = Field(..., min_length=1, max_length=128)
    action: Literal["none", "hint", "give_up"] = "none"
    conversation_id: int | None = Field(
        None,
        description="ID диалога в БД (только для авторизованных; session_id = session_key диалога)",
    )
    memory_user_id: str | None = Field(
        None,
        max_length=128,
        description="Стабильный id для долговременной памяти (иначе session_id)",
    )
    client_message_id: str | None = Field(
        None,
        max_length=64,
        description="Идентификатор клиентского сообщения для дедупликации повторных отправок",
    )
    assignment_id: int | None = Field(
        None,
        description="Назначение/домашнее задание, с которым связан диалог",
    )


class MemoryOut(BaseModel):
    topics: list[str] = Field(default_factory=list)
    mistakes: list[dict[str, Any]] = Field(default_factory=list)
    progress: dict[str, str] = Field(default_factory=dict)
    user_type: str = "lazy"
    skill_status: dict[str, str] = Field(default_factory=dict)
    thinking_profile: dict[str, Any] = Field(default_factory=dict)


class FallacyOut(BaseModel):
    has_fallacy: bool = False
    fallacy_type: str | None = None
    fallacy_description: str | None = None
    suggestion: str | None = None


class PedagogyOut(BaseModel):
    mode: str = "friendly"
    difficulty_level: int = 1
    last_response_depth: float = 0.0
    fallacy: FallacyOut = Field(default_factory=FallacyOut)


class ChatResponse(BaseModel):
    reply: str
    mode: str
    attempts: int
    frustration: int
    frustration_level: int  # 0..3 для UI (анти-фрустрация)
    user_type: str  # lazy | anxious | thinker
    topic: str
    memory: MemoryOut
    skill_tree: dict[str, Any]
    pedagogy: PedagogyOut
    persisted_user_message_id: int | None = None
    persisted_assistant_message_id: int | None = None
    conversation_id: int | None = None
    session_key: str | None = None


def _line_for_memory_update(body: ChatRequest) -> str:
    m = (body.message or "").strip()
    if body.action == "give_up":
        return m or "(сдаюсь — нужно краткое объяснение и контрольный вопрос в конце)"
    if body.action == "hint":
        return m or "(запрошена подсказка)"
    return m


def _initial_conversation_title(body: ChatRequest) -> str:
    seed = (body.message or "").strip()
    if not seed:
        seed = _line_for_memory_update(body)
    seed = seed.strip()
    if not seed or seed.startswith("("):
        return "Новый диалог"
    return seed[:50]


def _sse_event(event: str, data: Any) -> str:
    payload = data if isinstance(data, str) else json.dumps(data, ensure_ascii=False)
    return f"event: {event}\ndata: {payload}\n\n"


async def _prepare_chat_turn(
    body: ChatRequest,
    r: Any,
    db_user: User | None,
) -> tuple[PreparedChatTurn, ChatResponse | None]:
    msg_stripped = (body.message or "").strip()
    idle_turn = body.action == "none" and not msg_stripped
    active_conversation_id = body.conversation_id
    active_assignment_id = body.assignment_id

    if db_user and active_assignment_id is not None:

        def _verify_assignment() -> int | None:
            with SessionLocal() as db:
                a = db.get(Assignment, active_assignment_id)
                if a is None:
                    return None
                if db_user.role == "admin":
                    return a.id
                row = db.execute(
                    select(ClassStudent).where(
                        ClassStudent.class_id == a.class_id,
                        ClassStudent.student_id == db_user.id,
                    )
                ).scalar_one_or_none()
                return a.id if row is not None else None

        checked_assignment_id = await run_in_threadpool(_verify_assignment)
        if checked_assignment_id is None:
            raise HTTPException(status_code=404, detail="Assignment not found")
        active_assignment_id = checked_assignment_id

    if db_user and not idle_turn and active_conversation_id is None:

        def _ensure_conv() -> int:
            with SessionLocal() as db:
                c = get_or_create_conversation_by_session_key(
                    db,
                    db_user.id,
                    body.session_id,
                    _initial_conversation_title(body),
                    assignment_id=active_assignment_id,
                )
                return c.id

        active_conversation_id = await run_in_threadpool(_ensure_conv)

    if active_conversation_id is not None:
        if db_user is None:
            raise HTTPException(status_code=401, detail="Authentication required when conversation_id is set")

        def _verify_conv() -> str | None:
            with SessionLocal() as db:
                c = get_owned_conversation(db, db_user.id, active_conversation_id)
                return c.session_key if c else None

        sk = await run_in_threadpool(_verify_conv)
        if sk is None:
            raise HTTPException(status_code=404, detail="Conversation not found")
        if body.session_id != sk:
            raise HTTPException(
                status_code=400,
                detail="session_id must equal conversation.session_key for this conversation",
            )

    state = await load_state(r, body.session_id)
    if db_user and active_conversation_id is not None:

        def _hydr_history() -> None:
            with SessionLocal() as db:
                hydrate_state_history_from_conversation_if_empty(
                    db, db_user.id, active_conversation_id, state
                )

        await run_in_threadpool(_hydr_history)

    mid = str(db_user.id) if db_user else (body.memory_user_id or body.session_id).strip()
    memory = await load_memory(r, mid)
    if memory.user_type in ("lazy", "anxious", "thinker"):
        state.user_type = memory.user_type
    prev_skill = dict(memory.skill_status)
    pedagogy_state = await load_pedagogy(r, body.session_id)

    persistent_profile = ""
    russian_only = True
    if db_user:

        def _hydrate_and_profile() -> tuple[str, str, bool]:
            with SessionLocal() as db:
                hydrate_session_pedagogy_from_db(db, db_user.id, pedagogy_state)
                tm = get_tutor_mode(db, db_user.id)
                prof = build_persistent_profile_for_prompt(db, db_user.id)
                ru = get_russian_only(db, db_user.id)
                return tm, prof, ru

        tm, persistent_profile, russian_only = await run_in_threadpool(_hydrate_and_profile)
        try:
            pedagogy_state.mode = TutorMode(tm)
        except ValueError:
            pass

    cheat = bool(msg_stripped and is_cheating(msg_stripped))

    def _make_router() -> ModelRouter:
        if db_user is None:
            return ModelRouter()
        with SessionLocal() as db:
            return build_model_router_for_user(db, db_user.id)

    router = await run_in_threadpool(_make_router)

    if db_user and active_conversation_id is not None and not idle_turn and body.client_message_id:

        def _find_duplicate() -> tuple[int, int, str, dict[str, Any] | None] | None:
            with SessionLocal() as db:
                pair = find_duplicate_turn(
                    db,
                    db_user.id,
                    active_conversation_id,
                    body.client_message_id or "",
                )
                if pair is None:
                    return None
                user_msg, tutor_msg = pair
                return (
                    user_msg.id,
                    tutor_msg.id,
                    tutor_msg.content,
                    user_msg.fallacy_detected if isinstance(user_msg.fallacy_detected, dict) else None,
                )

        duplicate = await run_in_threadpool(_find_duplicate)
        if duplicate is not None:
            user_mid, tutor_mid, stored_reply, stored_fallacy = duplicate
            tree_hint = resolve_track_hint(state.topic, memory, body.message)
            subj = canonical_subject_topic(msg_stripped)
            if subj:
                tree_hint = f"{subj} {tree_hint}".strip()
            tree_hint = align_tree_hint_with_session_topic(tree_hint, state.topic)
            skill_tree = build_skill_tree_payload(
                dict(memory.skill_status), dict(memory.skill_status), track_hint=tree_hint, topic=state.topic
            )
            ut = state.user_type if state.user_type in ("lazy", "anxious", "thinker") else "lazy"
            md = memory.to_dict()
            fal = FallacyOut()
            if stored_fallacy:
                fal = FallacyOut(
                    has_fallacy=bool(stored_fallacy.get("has_fallacy")),
                    fallacy_type=stored_fallacy.get("fallacy_type"),
                    fallacy_description=stored_fallacy.get("fallacy_description"),
                    suggestion=stored_fallacy.get("suggestion"),
                )
            return (
                PreparedChatTurn(
                    body=body,
                    redis_client=r,
                    db_user=db_user,
                    msg_stripped=msg_stripped,
                    idle_turn=idle_turn,
                    active_conversation_id=active_conversation_id,
                    state=state,
                    memory=memory,
                    mid=mid,
                    prev_skill=prev_skill,
                    pedagogy_state=pedagogy_state,
                    persistent_profile=persistent_profile,
                    russian_only=russian_only,
                    cheat=cheat,
                    router=router,
                    analysis=None,
                ),
                ChatResponse(
                    reply=stored_reply,
                    mode=state.mode,
                    attempts=state.attempts,
                    frustration=state.frustration,
                    frustration_level=min(3, state.frustration),
                    user_type=ut,
                    topic=state.topic,
                    memory=MemoryOut(
                        topics=md["topics"],
                        mistakes=md["mistakes"],
                        progress=md["progress"],
                        user_type=md["user_type"],
                        skill_status=md.get("skill_status") or {},
                        thinking_profile=md.get("thinking_profile") or {},
                    ),
                    skill_tree=skill_tree,
                    pedagogy=PedagogyOut(
                        mode=_pedagogy_mode_str(pedagogy_state.mode),
                        difficulty_level=pedagogy_state.difficulty_level,
                        last_response_depth=round(pedagogy_state.last_response_depth, 3),
                        fallacy=fal,
                    ),
                    persisted_user_message_id=user_mid,
                    persisted_assistant_message_id=tutor_mid,
                    conversation_id=active_conversation_id,
                    session_key=body.session_id,
                ),
            )

    analysis: dict[str, Any] | None = None
    if not cheat and not idle_turn and body.action == "none" and msg_stripped:
        analysis = await analyze_response(
            router,
            msg_stripped,
            _last_assistant_question(state.history),
            _history_to_text(state.history, max_messages=10),
        )
        if analysis.get("has_fallacy"):
            ft = str(analysis.get("fallacy_type") or "")
            if ft and ft != "none" and ft not in pedagogy_state.common_fallacies:
                pedagogy_state.common_fallacies.append(ft)
                pedagogy_state.common_fallacies = pedagogy_state.common_fallacies[-15:]

    return (
        PreparedChatTurn(
            body=body,
            redis_client=r,
            db_user=db_user,
            msg_stripped=msg_stripped,
            idle_turn=idle_turn,
            active_conversation_id=active_conversation_id,
            state=state,
            memory=memory,
            mid=mid,
            prev_skill=prev_skill,
            pedagogy_state=pedagogy_state,
            persistent_profile=persistent_profile,
            russian_only=russian_only,
            cheat=cheat,
            router=router,
            analysis=analysis,
        ),
        None,
    )


async def _finalize_chat_turn(prepared: PreparedChatTurn, reply: str, mode: str) -> ChatResponse:
    body = prepared.body
    r = prepared.redis_client
    state = prepared.state
    memory = prepared.memory
    pedagogy_state = prepared.pedagogy_state
    analysis = prepared.analysis

    await save_state(r, body.session_id, state)

    if not prepared.cheat and not prepared.idle_turn:
        memory = update_memory_after_turn(memory, state, _line_for_memory_update(body), mode)
        await save_memory(r, prepared.mid, memory)

    if body.action == "hint":
        apply_hint_penalty(pedagogy_state)
    elif body.action == "none" and prepared.msg_stripped and not prepared.cheat and analysis is not None:
        apply_after_user_turn(pedagogy_state, float(analysis.get("depth_combined") or 0.0))

    await save_pedagogy(r, body.session_id, pedagogy_state)

    if prepared.db_user and get_settings().skill_update_enabled:
        if (
            not prepared.cheat
            and not prepared.idle_turn
            and body.action == "none"
            and prepared.msg_stripped
            and analysis is not None
        ):
            uid = prepared.db_user.id
            ut = prepared.msg_stripped
            an = dict(analysis)
            dl = int(pedagogy_state.difficulty_level)

            async def _learning_bg() -> None:
                try:
                    await run_in_threadpool(
                        update_user_learning_progress_sync, uid, ut, an, dl
                    )
                except Exception:
                    log.exception("learning progress background task failed")

            asyncio.create_task(_learning_bg())

    tree_hint = resolve_track_hint(state.topic, memory, body.message)
    subj = canonical_subject_topic(prepared.msg_stripped)
    if subj:
        tree_hint = f"{subj} {tree_hint}".strip()
    tree_hint = align_tree_hint_with_session_topic(tree_hint, state.topic)
    skill_tree = build_skill_tree_payload(
        prepared.prev_skill, dict(memory.skill_status), track_hint=tree_hint, topic=state.topic
    )

    ut = state.user_type if state.user_type in ("lazy", "anxious", "thinker") else "lazy"
    md = memory.to_dict()

    fal = FallacyOut()
    if analysis:
        fal = FallacyOut(
            has_fallacy=bool(analysis.get("has_fallacy")),
            fallacy_type=(analysis.get("fallacy_type") if analysis.get("has_fallacy") else None),
            fallacy_description=(
                analysis.get("fallacy_description") if analysis.get("has_fallacy") else None
            ),
            suggestion=analysis.get("suggestion") if analysis.get("has_fallacy") else None,
        )

    ped_out = PedagogyOut(
        mode=_pedagogy_mode_str(pedagogy_state.mode),
        difficulty_level=pedagogy_state.difficulty_level,
        last_response_depth=round(pedagogy_state.last_response_depth, 3),
        fallacy=fal,
    )

    persisted_pair: tuple[int, int] | None = None
    if prepared.db_user and prepared.active_conversation_id and not prepared.idle_turn:
        user_line = (
            prepared.msg_stripped
            if body.action == "none" and prepared.msg_stripped
            else _line_for_memory_update(body)
        )
        fallacy_payload: dict[str, Any] | None = None
        if analysis:
            fallacy_payload = {
                "has_fallacy": bool(analysis.get("has_fallacy")),
                "fallacy_type": analysis.get("fallacy_type"),
                "fallacy_description": analysis.get("fallacy_description"),
                "suggestion": analysis.get("suggestion"),
                "depth_combined": analysis.get("depth_combined"),
            }
        cid = prepared.active_conversation_id
        uid = prepared.db_user.id

        def _persist_turn() -> tuple[int, int] | None:
            with SessionLocal() as db:
                return append_messages(
                    db,
                    cid,
                    uid,
                    user_line,
                    reply,
                    fallacy_payload,
                    client_message_id=body.client_message_id,
                )

        persisted_pair = await run_in_threadpool(_persist_turn)

    return ChatResponse(
        reply=reply,
        mode=mode,
        attempts=state.attempts,
        frustration=state.frustration,
        frustration_level=min(3, state.frustration),
        user_type=ut,
        topic=state.topic,
        memory=MemoryOut(
            topics=md["topics"],
            mistakes=md["mistakes"],
            progress=md["progress"],
            user_type=md["user_type"],
            skill_status=md.get("skill_status") or {},
            thinking_profile=md.get("thinking_profile") or {},
        ),
        skill_tree=skill_tree,
        pedagogy=ped_out,
        persisted_user_message_id=persisted_pair[0] if persisted_pair else None,
        persisted_assistant_message_id=persisted_pair[1] if persisted_pair else None,
        conversation_id=prepared.active_conversation_id,
        session_key=body.session_id,
    )


def _guard_tutor_reply(reply: str, *, session_id: str, conversation_id: int | None, source: str) -> str:
    text = str(reply or "").strip()
    if not is_tutor_answering_for_student(text):
        return text
    log.warning(
        "tutor reply blocked by route guard source=%s session_id=%s conversation_id=%s response=%r",
        source,
        session_id,
        conversation_id,
        text[:200],
    )
    return _SAFE_TUTOR_FALLBACK


def _sync_last_assistant_reply(state: Any, original_reply: str, guarded_reply: str) -> None:
    if original_reply == guarded_reply:
        return
    history = getattr(state, "history", None)
    if not isinstance(history, list):
        return
    for item in reversed(history):
        if not isinstance(item, dict):
            continue
        if item.get("role") != "assistant":
            continue
        if str(item.get("content") or "").strip() == str(original_reply or "").strip():
            item["content"] = guarded_reply
        return


@router.post("/chat", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    r=Depends(redis_dep),
    db_user: User | None = Depends(get_current_user_optional),
):
    prepared, duplicate = await _prepare_chat_turn(body, r, db_user)
    if duplicate is not None:
        return duplicate

    fallacy_instr = ""
    if prepared.analysis is not None:
        fallacy_instr = build_fallacy_instruction(
            _pedagogy_mode_str(prepared.pedagogy_state.mode),
            prepared.analysis,
        )

    pctx = PedagogyTurnContext(
        tutor_mode=_pedagogy_mode_str(prepared.pedagogy_state.mode),
        difficulty_level=prepared.pedagogy_state.difficulty_level,
        russian_only=prepared.russian_only,
        fallacy_instruction=fallacy_instr,
        persistent_profile=prepared.persistent_profile,
    )

    controller = TutorController(prepared.router)
    try:
        reply, mode = await controller.handle_turn(
            prepared.state, body.message, body.action, prepared.memory, pedagogy=pctx
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
    original_reply = reply
    reply = _guard_tutor_reply(
        reply,
        session_id=body.session_id,
        conversation_id=prepared.active_conversation_id,
        source="chat",
    )
    _sync_last_assistant_reply(prepared.state, original_reply, reply)

    return await _finalize_chat_turn(prepared, reply, mode)


@router.post("/chat/message/stream")
async def chat_message_stream(
    body: ChatRequest,
    http_request: Request,
    r=Depends(redis_dep),
    db_user: User | None = Depends(get_current_user_optional),
):
    prepared, duplicate = await _prepare_chat_turn(body, r, db_user)
    if duplicate is not None:

        async def _duplicate_stream() -> AsyncGenerator[str, None]:
            yield _sse_event(
                "meta",
                {
                    "conversation_id": duplicate.conversation_id,
                    "session_key": duplicate.session_key,
                },
            )
            yield _sse_event("done", duplicate.model_dump())

        return StreamingResponse(_duplicate_stream(), media_type="text/event-stream")

    fallacy_instr = ""
    if prepared.analysis is not None:
        fallacy_instr = build_fallacy_instruction(
            _pedagogy_mode_str(prepared.pedagogy_state.mode),
            prepared.analysis,
        )

    pctx = PedagogyTurnContext(
        tutor_mode=_pedagogy_mode_str(prepared.pedagogy_state.mode),
        difficulty_level=prepared.pedagogy_state.difficulty_level,
        russian_only=prepared.russian_only,
        fallacy_instruction=fallacy_instr,
        persistent_profile=prepared.persistent_profile,
    )

    controller = TutorController(prepared.router)

    async def _event_stream() -> AsyncGenerator[str, None]:
        parts: list[str] = []
        mode = prepared.state.mode
        started = False
        try:
            yield _sse_event(
                "meta",
                {
                    "conversation_id": prepared.active_conversation_id,
                    "session_key": body.session_id,
                },
            )
            async for chunk in controller.stream_turn(
                prepared.state,
                body.message,
                body.action,
                prepared.memory,
                pedagogy=pctx,
            ):
                if await http_request.is_disconnected():
                    raise asyncio.CancelledError()
                mode = prepared.state.mode
                if not chunk:
                    continue
                started = True
                parts.append(chunk)
                yield _sse_event("chunk", chunk)
            original_reply = "".join(parts).strip() or "…"
            reply = _guard_tutor_reply(
                original_reply,
                session_id=body.session_id,
                conversation_id=prepared.active_conversation_id,
                source="chat_stream",
            )
            _sync_last_assistant_reply(prepared.state, original_reply, reply)
            response = await _finalize_chat_turn(prepared, reply, mode)
            yield _sse_event("done", response.model_dump())
        except asyncio.CancelledError:
            log.info("chat stream cancelled session_id=%s conversation_id=%s", body.session_id, prepared.active_conversation_id)
            raise
        except Exception as e:
            log.exception("chat stream failed")
            if not started:
                yield _sse_event("error", {"message": str(e)})

    return StreamingResponse(
        _event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
