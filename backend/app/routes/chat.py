from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.deps import redis_dep
from app.models.pedagogy import PedagogyTurnContext
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
from app.services.skill_tree_manager import build_skill_tree_payload
from app.services.tutor_controller import TutorController

router = APIRouter()


def _last_assistant_question(history: list[dict[str, Any]]) -> str:
    for h in reversed(history):
        if h.get("role") == "assistant":
            return str(h.get("content") or "").strip()
    return ""


class ChatRequest(BaseModel):
    message: str = ""
    session_id: str = Field(..., min_length=1, max_length=128)
    action: Literal["none", "hint", "give_up"] = "none"
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
):
    state = await load_state(r, body.session_id)
    mid = (body.memory_user_id or body.session_id).strip()
    memory = await load_memory(r, mid)
    prev_skill = dict(memory.skill_status)
    pedagogy_state = await load_pedagogy(r, body.session_id)

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
        fallacy_instr = build_fallacy_instruction(pedagogy_state.mode.value, analysis)
        if analysis.get("has_fallacy"):
            ft = str(analysis.get("fallacy_type") or "")
            if ft and ft != "none" and ft not in pedagogy_state.common_fallacies:
                pedagogy_state.common_fallacies.append(ft)
                pedagogy_state.common_fallacies = pedagogy_state.common_fallacies[-15:]

    pctx = PedagogyTurnContext(
        tutor_mode=pedagogy_state.mode.value,
        difficulty_level=pedagogy_state.difficulty_level,
        fallacy_instruction=fallacy_instr,
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

    skill_tree = build_skill_tree_payload(prev_skill, dict(memory.skill_status), state.topic)

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
        mode=pedagogy_state.mode.value,
        difficulty_level=pedagogy_state.difficulty_level,
        last_response_depth=round(pedagogy_state.last_response_depth, 3),
        fallacy=fal,
    )

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
    )
