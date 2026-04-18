"""API геймификации: очки мудрости, достижения, ежедневные вызовы."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from app.api.deps_auth import get_current_user_optional
from app.db.models import User
from app.db.session import SessionLocal
from app.deps import redis_dep
from app.models.gamification import (
    ACHIEVEMENTS,
    UserProgressPublic,
    challenge_text,
    ensure_challenge_day,
    process_user_response,
    reset_session_counters,
    state_to_public,
)
from app.services.db_gamification import apply_redis_state_to_db
from app.services.gamification_store import load_progress, save_progress

router = APIRouter()


def _utc_today():
    return datetime.now(timezone.utc).date()


class GamificationActionBody(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=128)
    action_type: Literal["user_response", "new_dialog"] = "user_response"
    dialog_context: dict[str, Any] = Field(default_factory=dict)


class GamificationActionResponse(BaseModel):
    progress: UserProgressPublic
    new_achievements: list[str] = Field(default_factory=list)
    toasts: list[str] = Field(default_factory=list)


class DailyChallengeResponse(BaseModel):
    challenge_id: str | None
    challenge_text: str
    completed: bool


@router.get("/progress/{session_id}", response_model=UserProgressPublic)
async def get_progress(session_id: str, r=Depends(redis_dep)):
    state = await load_progress(r, session_id)
    today = _utc_today()
    ensure_challenge_day(state, today)
    await save_progress(r, session_id, state)
    return state_to_public(state)


@router.post("/action", response_model=GamificationActionResponse)
async def post_action(
    body: GamificationActionBody,
    r=Depends(redis_dep),
    db_user: User | None = Depends(get_current_user_optional),
):
    state = await load_progress(r, body.session_id)
    today = _utc_today()
    ensure_challenge_day(state, today)
    new_ach: list[str] = []
    toasts: list[str] = []

    if body.action_type == "new_dialog":
        reset_session_counters(state)
    elif body.action_type == "user_response":
        t, new_ach = process_user_response(state, body.dialog_context, today)
        toasts.extend(t)

    await save_progress(r, body.session_id, state)
    if db_user:

        def _sync() -> None:
            with SessionLocal() as db:
                apply_redis_state_to_db(db, db_user.id, state)

        await run_in_threadpool(_sync)
    return GamificationActionResponse(
        progress=state_to_public(state),
        new_achievements=new_ach,
        toasts=toasts,
    )


@router.get("/achievements")
async def list_achievements():
    return {"achievements": [a.model_dump() for a in ACHIEVEMENTS]}


@router.get("/daily-challenge/{session_id}", response_model=DailyChallengeResponse)
async def get_daily_challenge(session_id: str, r=Depends(redis_dep)):
    state = await load_progress(r, session_id)
    today = _utc_today()
    ensure_challenge_day(state, today)
    await save_progress(r, session_id, state)
    cid = state.daily_challenge_id
    return DailyChallengeResponse(
        challenge_id=cid,
        challenge_text=challenge_text(cid),
        completed=state.daily_challenge_completed,
    )
