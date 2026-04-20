from __future__ import annotations

import asyncio
import logging
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from app.api.deps_auth import get_current_user_optional
from app.db.models import User
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
from app.services.conversation_db import (
    append_messages,
    get_owned_conversation,
    hydrate_state_history_from_conversation_if_empty,
)
from app.services.learning_service import (
    build_persistent_profile_for_prompt,
    hydrate_session_pedagogy_from_db,
    update_user_learning_progress_sync,
)
from app.services.user_settings_db import get_tutor_mode

router = APIRouter()
log = logging.getLogger(__name__)


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


def _line_for_memory_update(body: ChatRequest) -> str:
    m = (body.message or "").strip()
    if body.action == "give_up":
        return m or "(сдаюсь — нужно краткое объяснение и контрольный вопрос в конце)"
    if body.action == "hint":
        return m or "(запрошена подсказка)"
    return m


@router.post("/chat", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    r=Depends(redis_dep),
    db_user: User | None = Depends(get_current_user_optional),
):
    if body.conversation_id is not None:
        if db_user is None:
            raise HTTPException(status_code=401, detail="Authentication required when conversation_id is set")

        def _verify_conv() -> str | None:
            with SessionLocal() as db:
                c = get_owned_conversation(db, db_user.id, body.conversation_id)
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
    if db_user and body.conversation_id is not None:

        def _hydr_history() -> None:
            with SessionLocal() as db:
                hydrate_state_history_from_conversation_if_empty(
                    db, db_user.id, body.conversation_id, state
                )

        await run_in_threadpool(_hydr_history)
    if db_user:
        mid = str(db_user.id)
    else:
        mid = (body.memory_user_id or body.session_id).strip()
    memory = await load_memory(r, mid)
    # Тип ученика хранится в долговременной памяти; новый session_id в Redis иначе даёт lazy («новичок»).
    if memory.user_type in ("lazy", "anxious", "thinker"):
        state.user_type = memory.user_type
    prev_skill = dict(memory.skill_status)
    pedagogy_state = await load_pedagogy(r, body.session_id)

    persistent_profile = ""
    if db_user:

        def _hydrate_and_profile() -> tuple[str, str]:
            with SessionLocal() as db:
                hydrate_session_pedagogy_from_db(db, db_user.id, pedagogy_state)
                tm = get_tutor_mode(db, db_user.id)
                prof = build_persistent_profile_for_prompt(db, db_user.id)
                return tm, prof

        tm, persistent_profile = await run_in_threadpool(_hydrate_and_profile)
        try:
            pedagogy_state.mode = TutorMode(tm)
        except ValueError:
            pass

    msg_stripped = (body.message or "").strip()
    cheat = bool(msg_stripped and is_cheating(msg_stripped))
    idle_turn = body.action == "none" and not msg_stripped

    analysis: dict[str, Any] | None = None
    fallacy_instr = ""
    if not cheat and not idle_turn and body.action == "none" and msg_stripped:
        router_a = ModelRouter()
        analysis = await analyze_response(
            router_a,
            msg_stripped,
            _last_assistant_question(state.history),
            _history_to_text(state.history, max_messages=10),
        )
        fallacy_instr = build_fallacy_instruction(_pedagogy_mode_str(pedagogy_state.mode), analysis)
        if analysis.get("has_fallacy"):
            ft = str(analysis.get("fallacy_type") or "")
            if ft and ft != "none" and ft not in pedagogy_state.common_fallacies:
                pedagogy_state.common_fallacies.append(ft)
                pedagogy_state.common_fallacies = pedagogy_state.common_fallacies[-15:]

    pctx = PedagogyTurnContext(
        tutor_mode=_pedagogy_mode_str(pedagogy_state.mode),
        difficulty_level=pedagogy_state.difficulty_level,
        fallacy_instruction=fallacy_instr,
        persistent_profile=persistent_profile,
    )

    router = ModelRouter()
    controller = TutorController(router)
    try:
        reply, mode = await controller.handle_turn(
            state, body.message, body.action, memory, pedagogy=pctx
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
    await save_state(r, body.session_id, state)

    if not cheat and not idle_turn:
        memory = update_memory_after_turn(memory, state, _line_for_memory_update(body), mode)
        await save_memory(r, mid, memory)

    if body.action == "hint":
        apply_hint_penalty(pedagogy_state)
    elif body.action == "none" and msg_stripped and not cheat and analysis is not None:
        apply_after_user_turn(pedagogy_state, float(analysis.get("depth_combined") or 0.0))

    await save_pedagogy(r, body.session_id, pedagogy_state)

    if db_user and get_settings().skill_update_enabled:
        if (
            not cheat
            and not idle_turn
            and body.action == "none"
            and msg_stripped
            and analysis is not None
        ):
            uid = db_user.id
            ut = msg_stripped
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
    subj = canonical_subject_topic(msg_stripped)
    if subj:
        tree_hint = f"{subj} {tree_hint}".strip()
    tree_hint = align_tree_hint_with_session_topic(tree_hint, state.topic)
    skill_tree = build_skill_tree_payload(
        prev_skill, dict(memory.skill_status), track_hint=tree_hint, topic=state.topic
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
    if db_user and body.conversation_id and not cheat and not idle_turn:
        user_line = (
            msg_stripped
            if body.action == "none" and msg_stripped
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
        cid = body.conversation_id
        uid = db_user.id
        rep = reply

        def _persist_turn() -> tuple[int, int] | None:
            with SessionLocal() as db:
                return append_messages(db, cid, uid, user_line, rep, fallacy_payload)

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
    )
