"""API геймификации: очки мудрости, достижения, ежедневные вызовы."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from app.api.deps_auth import get_current_user, get_current_user_optional
from app.db.models import GamificationProgress, User
from app.db.session import SessionLocal
from app.deps import redis_dep
from app.models.gamification import (
    ACHIEVEMENTS,
    UserProgressPublic,
    UserProgressState,
    challenge_text,
    ensure_challenge_day,
    merge_user_progress_states,
    process_user_response,
    reset_session_counters,
    state_to_public,
)
from app.services.db_gamification import apply_redis_state_to_db, user_progress_state_from_row
from app.services.gamification_store import load_progress, save_progress

router = APIRouter()


async def _resolve_gamification_state(
    redis,
    session_id: str,
    db_user: User | None,
) -> UserProgressState:
    """
    Гость — только Redis по session_id.
    Авторизованный — всегда объединяем Redis (ключ user:id), БД и гостевой ключ сессии:
    иначе при redis_hit и нулях в Redis прогресс из БД никогда не подмешивался.
    """
    uid = db_user.id if db_user else None
    state_r, _hit = await load_progress(redis, session_id, uid)

    if uid is None:
        return state_r

    def _from_db():
        with SessionLocal() as db:
            row = db.get(GamificationProgress, uid)
            return user_progress_state_from_row(row, fallback_user_id=str(uid))

    state_db = await run_in_threadpool(_from_db)
    if state_db is None:
        state_db = UserProgressState(user_id=str(uid))

    state = merge_user_progress_states(state_r, state_db)

    # Не мержить «гостя» для виртуального session_id=me — это общий ключ gamification:me в Redis.
    sid_norm = session_id.strip().lower()
    if sid_norm != "me":
        guest_r, guest_hit = await load_progress(redis, session_id, None)
        if guest_hit:
            state = merge_user_progress_states(state, guest_r)

    state.user_id = str(uid)
    await save_progress(redis, session_id, state, uid)
    return state


async def _persist_progress_to_db_if_auth(db_user: User | None, state: UserProgressState) -> None:
    if db_user is None:
        return

    def _sync() -> None:
        with SessionLocal() as db:
            apply_redis_state_to_db(db, db_user.id, state)

    await run_in_threadpool(_sync)


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


@router.get("/me/progress", response_model=UserProgressPublic)
async def get_progress_me(
    r=Depends(redis_dep),
    db_user: User = Depends(get_current_user),
):
    """Прогресс аккаунта без привязки к session_id (надёжнее для UI при смене диалога)."""
    state = await _resolve_gamification_state(r, "me", db_user)
    today = _utc_today()
    ensure_challenge_day(state, today)
    await save_progress(r, "me", state, db_user.id)
    await _persist_progress_to_db_if_auth(db_user, state)
    return state_to_public(state)


@router.get("/progress/{session_id}", response_model=UserProgressPublic)
async def get_progress(
    session_id: str,
    r=Depends(redis_dep),
    db_user: User | None = Depends(get_current_user_optional),
):
    state = await _resolve_gamification_state(r, session_id, db_user)
    today = _utc_today()
    ensure_challenge_day(state, today)
    await save_progress(r, session_id, state, db_user.id if db_user else None)
    await _persist_progress_to_db_if_auth(db_user, state)
    return state_to_public(state)


@router.post("/action", response_model=GamificationActionResponse)
async def post_action(
    body: GamificationActionBody,
    r=Depends(redis_dep),
    db_user: User | None = Depends(get_current_user_optional),
):
    state = await _resolve_gamification_state(r, body.session_id, db_user)
    today = _utc_today()
    ensure_challenge_day(state, today)
    new_ach: list[str] = []
    toasts: list[str] = []

    if body.action_type == "new_dialog":
        reset_session_counters(state)
    elif body.action_type == "user_response":
        t, new_ach = process_user_response(state, body.dialog_context, today)
        toasts.extend(t)

    await save_progress(r, body.session_id, state, db_user.id if db_user else None)
    await _persist_progress_to_db_if_auth(db_user, state)
    return GamificationActionResponse(
        progress=state_to_public(state),
        new_achievements=new_ach,
        toasts=toasts,
    )


@router.get("/achievements")
async def list_achievements():
    return {"achievements": [a.model_dump() for a in ACHIEVEMENTS]}


@router.get("/me/daily-challenge", response_model=DailyChallengeResponse)
async def get_daily_challenge_me(
    r=Depends(redis_dep),
    db_user: User = Depends(get_current_user),
):
    state = await _resolve_gamification_state(r, "me", db_user)
    today = _utc_today()
    ensure_challenge_day(state, today)
    await save_progress(r, "me", state, db_user.id)
    await _persist_progress_to_db_if_auth(db_user, state)
    cid = state.daily_challenge_id
    return DailyChallengeResponse(
        challenge_id=cid,
        challenge_text=challenge_text(cid),
        completed=state.daily_challenge_completed,
    )


@router.get("/daily-challenge/{session_id}", response_model=DailyChallengeResponse)
async def get_daily_challenge(
    session_id: str,
    r=Depends(redis_dep),
    db_user: User | None = Depends(get_current_user_optional),
):
    state = await _resolve_gamification_state(r, session_id, db_user)
    today = _utc_today()
    ensure_challenge_day(state, today)
    await save_progress(r, session_id, state, db_user.id if db_user else None)
    await _persist_progress_to_db_if_auth(db_user, state)
    cid = state.daily_challenge_id
    return DailyChallengeResponse(
        challenge_id=cid,
        challenge_text=challenge_text(cid),
        completed=state.daily_challenge_completed,
    )
