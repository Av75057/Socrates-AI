from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.config import Settings, get_settings
from app.services.redis_state import get_redis, load_state, save_state
from app.services.tutor_controller import TutorController

router = APIRouter()


class ChatRequest(BaseModel):
    message: str = ""
    session_id: str = Field(..., min_length=1, max_length=128)
    action: Literal["none", "hint", "give_up"] = "none"


class ChatResponse(BaseModel):
    reply: str
    mode: str
    attempts: int
    frustration: int
    frustration_level: int  # 0..3 для UI (анти-фрустрация)
    user_type: str  # lazy | anxious | thinker
    topic: str


_redis = None


async def redis_dep(settings: Settings = Depends(get_settings)):
    global _redis
    if _redis is None:
        _redis = await get_redis(settings.redis_url)
    return _redis


@router.post("/chat", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    r=Depends(redis_dep),
):
    state = await load_state(r, body.session_id)
    controller = TutorController()
    try:
        reply, mode = await controller.handle_turn(state, body.message, body.action)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
    await save_state(r, body.session_id, state)
    ut = state.user_type if state.user_type in ("lazy", "anxious", "thinker") else "lazy"
    return ChatResponse(
        reply=reply,
        mode=mode,
        attempts=state.attempts,
        frustration=state.frustration,
        frustration_level=min(3, state.frustration),
        user_type=ut,
        topic=state.topic,
    )
