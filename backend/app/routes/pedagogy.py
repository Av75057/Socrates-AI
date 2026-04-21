"""Педагогика: режим тьютора, анализ ответа, подсказка."""

from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from app.api.deps_auth import get_current_user_optional
from app.db.models import User
from app.db.session import SessionLocal
from app.deps import redis_dep
from app.models.pedagogy import TutorMode, UserPedagogyState
from app.services.fallacy_detector import analyze_response
from app.services.difficulty_adjuster import apply_hint_penalty
from app.services.model_router import ModelRouter
from app.services.pedagogy_store import load_pedagogy, save_pedagogy
from app.services.user_settings_db import build_model_router_for_user

router = APIRouter()


class AnalyzeBody(BaseModel):
    user_response: str = Field(..., min_length=1)
    question: str = ""
    dialog_history: str = ""


class AnalyzeResponse(BaseModel):
    has_fallacy: bool
    fallacy_type: str
    fallacy_description: str
    suggestion: str
    depth_heuristic: float
    depth_llm: float
    depth_combined: float


class ModeBody(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=128)
    mode: Literal["strict", "friendly", "provocateur"]


class HintBody(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=128)
    topic: str = ""
    last_user_message: str = ""


class HintResponse(BaseModel):
    hint: str
    difficulty_level: int


async def _router_for_user(db_user: User | None) -> ModelRouter:
    def _sync() -> ModelRouter:
        if db_user is None:
            return ModelRouter()
        with SessionLocal() as db:
            return build_model_router_for_user(db, db_user.id)

    return await run_in_threadpool(_sync)


def _state_public(s: UserPedagogyState) -> dict[str, Any]:
    return {
        "session_id": s.session_id,
        "mode": s.mode.value,
        "difficulty_level": s.difficulty_level,
        "last_response_depth": round(s.last_response_depth, 3),
        "common_fallacies": list(s.common_fallacies),
    }


@router.post("/analyze", response_model=AnalyzeResponse)
async def pedagogy_analyze(
    body: AnalyzeBody,
    db_user: User | None = Depends(get_current_user_optional),
):
    r = await _router_for_user(db_user)
    data = await analyze_response(r, body.user_response, body.question, body.dialog_history)
    return AnalyzeResponse(
        has_fallacy=bool(data.get("has_fallacy")),
        fallacy_type=str(data.get("fallacy_type") or "none"),
        fallacy_description=str(data.get("fallacy_description") or ""),
        suggestion=str(data.get("suggestion") or ""),
        depth_heuristic=float(data.get("depth_heuristic") or 0),
        depth_llm=float(data.get("depth_llm") or 0),
        depth_combined=float(data.get("depth_combined") or 0),
    )


@router.get("/state/{session_id}")
async def get_pedagogy_state(session_id: str, redis=Depends(redis_dep)):
    s = await load_pedagogy(redis, session_id)
    return _state_public(s)


@router.get("/mode/{session_id}")
async def get_mode(session_id: str, redis=Depends(redis_dep)):
    s = await load_pedagogy(redis, session_id)
    return {"mode": s.mode.value}


@router.post("/mode")
async def set_mode(body: ModeBody, redis=Depends(redis_dep)):
    s = await load_pedagogy(redis, body.session_id)
    s.mode = TutorMode(body.mode)
    await save_pedagogy(redis, body.session_id, s)
    return _state_public(s)


@router.post("/hint", response_model=HintResponse)
async def pedagogy_hint(
    body: HintBody,
    redis=Depends(redis_dep),
    db_user: User | None = Depends(get_current_user_optional),
):
    s = await load_pedagogy(redis, body.session_id)
    apply_hint_penalty(s)
    router = await _router_for_user(db_user)
    model = router.pedagogy_model()
    messages = [
        {
            "role": "system",
            "content": (
                "Ты наставник Socrates AI. Дай одну короткую подсказку по теме (2–3 предложения), "
                "без полного решения и без лекции. Только русский язык, без эмодзи и без «странных» символов."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Тема: {body.topic or 'не указана'}\n"
                f"Последняя реплика ученика: {body.last_user_message or '(нет)'}\n"
                f"Текущая сложность диалога (1–5): {s.difficulty_level}. "
                "Сделай наводку, чтобы ученик сам додумал."
            ),
        },
    ]
    hint_text = await router.call_model(messages, model)
    if not hint_text or hint_text.startswith("[OpenRouter]") or hint_text.startswith("[LLM]"):
        hint_text = (
            "Попробуй ответить в два шага: сначала опиши своими словами, что ты уже понимаешь, "
            "потом скажи, что именно остаётся неясным."
        )
    await save_pedagogy(redis, body.session_id, s)
    return HintResponse(hint=hint_text.strip(), difficulty_level=s.difficulty_level)
