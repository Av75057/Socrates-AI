from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.deps import redis_dep
from app.services.cheat_detector import is_cheating
from app.services.memory_manager import update_memory_after_turn
from app.services.memory_store import load_memory, save_memory
from app.services.redis_state import load_state, save_state
from app.services.skill_tree_manager import build_skill_tree_payload
from app.services.tutor_controller import TutorController

router = APIRouter()


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
    controller = TutorController()
    try:
        reply, mode = await controller.handle_turn(
            state, body.message, body.action, memory
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
    await save_state(r, body.session_id, state)

    msg_stripped = (body.message or "").strip()
    cheat = bool(msg_stripped and is_cheating(msg_stripped))
    idle_turn = body.action == "none" and not msg_stripped
    if not cheat and not idle_turn:
        memory = update_memory_after_turn(memory, state, _line_for_memory_update(body), mode)
        await save_memory(r, mid, memory)

    skill_tree = build_skill_tree_payload(prev_skill, dict(memory.skill_status))

    ut = state.user_type if state.user_type in ("lazy", "anxious", "thinker") else "lazy"
    md = memory.to_dict()
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
    )
