from __future__ import annotations

import os
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps_auth import get_current_admin
from app.db.models import Conversation, GamificationProgress, Message, User, UserSettings
from app.db.session import get_db
from app.config import get_settings
from app.services.conversation_db import conversation_message_count
from app.services.learning_service import get_user_pedagogy_public, get_user_skills_summary
from app.services.llm.global_call import chat_completion_global_async
from app.services.llm.runtime import (
    get_effective_ollama_model,
    get_effective_provider,
    ping_ollama,
    runtime_snapshot,
    set_runtime_ollama_model,
    set_runtime_provider,
)
from app.services.model_router import ModelRouter

router = APIRouter(prefix="/admin", tags=["admin"])


class AdminUserSummary(BaseModel):
    id: int
    email: str
    full_name: str | None
    role: str
    is_active: bool
    wisdom_points: int


class AdminUserDetail(BaseModel):
    id: int
    email: str
    full_name: str | None
    role: str
    is_active: bool
    settings: dict[str, Any]
    gamification: dict[str, Any]
    learning: dict[str, Any]


class AdminUserUpdate(BaseModel):
    role: str | None = None
    is_active: bool | None = None
    wisdom_points: int | None = Field(None, ge=0)


class ConversationAdminSummary(BaseModel):
    id: int
    title: str
    started_at: str
    last_updated_at: str
    message_count: int


@router.get("/users", response_model=list[AdminUserSummary])
def admin_list_users(
    _: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
    q: str | None = Query(None, description="Поиск по email"),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    stmt = select(User).order_by(User.id.desc()).offset(offset).limit(limit)
    if q:
        stmt = stmt.where(User.email.ilike(f"%{q}%"))
    users = db.execute(stmt).scalars().all()
    out: list[AdminUserSummary] = []
    for u in users:
        g = db.get(GamificationProgress, u.id)
        wp = g.wisdom_points if g else 0
        out.append(
            AdminUserSummary(
                id=u.id,
                email=u.email,
                full_name=u.full_name,
                role=u.role,
                is_active=u.is_active,
                wisdom_points=wp,
            )
        )
    return out


def _admin_user_detail(db: Session, user_id: int) -> AdminUserDetail:
    u = db.get(User, user_id)
    if u is None:
        raise HTTPException(status_code=404, detail="User not found")
    s = db.execute(select(UserSettings).where(UserSettings.user_id == u.id)).scalar_one_or_none()
    g = db.get(GamificationProgress, u.id)
    return AdminUserDetail(
        id=u.id,
        email=u.email,
        full_name=u.full_name,
        role=u.role,
        is_active=u.is_active,
        settings={
            "tutor_mode": s.tutor_mode if s else "friendly",
            "theme": s.theme if s else None,
            "notifications_enabled": s.notifications_enabled if s else True,
        },
        gamification={
            "wisdom_points": g.wisdom_points if g else 0,
            "level": g.level if g else 1,
            "achievements": list(g.achievements) if g and g.achievements else [],
            "streak_days": g.streak_days if g else 0,
        },
        learning={
            "pedagogy": get_user_pedagogy_public(db, u.id),
            "skills": get_user_skills_summary(db, u.id),
        },
    )


@router.get("/users/{user_id}", response_model=AdminUserDetail)
def admin_get_user(user_id: int, _: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    return _admin_user_detail(db, user_id)


@router.put("/users/{user_id}", response_model=AdminUserDetail)
def admin_update_user(
    user_id: int,
    body: AdminUserUpdate,
    _: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    u = db.get(User, user_id)
    if u is None:
        raise HTTPException(status_code=404, detail="User not found")
    if body.role is not None:
        if body.role not in ("user", "admin", "educator"):
            raise HTTPException(status_code=400, detail="Invalid role")
        u.role = body.role
    if body.is_active is not None:
        u.is_active = body.is_active
    if body.wisdom_points is not None:
        g = db.get(GamificationProgress, u.id)
        if g is None:
            g = GamificationProgress(
                user_id=u.id,
                wisdom_points=body.wisdom_points,
                level=1,
                achievements=[],
                streak_days=0,
                last_daily_challenge_date=None,
                extra_state=None,
            )
            db.add(g)
        else:
            g.wisdom_points = body.wisdom_points
    db.commit()
    db.refresh(u)
    return _admin_user_detail(db, user_id)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def admin_delete_user(user_id: int, _: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    u = db.get(User, user_id)
    if u is None:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(u)
    db.commit()
    return None


@router.get("/users/{user_id}/conversations", response_model=list[ConversationAdminSummary])
def admin_user_conversations(
    user_id: int,
    _: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    u = db.get(User, user_id)
    if u is None:
        raise HTTPException(status_code=404, detail="User not found")
    rows = (
        db.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.last_updated_at.desc())
        )
        .scalars()
        .all()
    )
    return [
        ConversationAdminSummary(
            id=c.id,
            title=c.title,
            started_at=c.started_at.isoformat(),
            last_updated_at=c.last_updated_at.isoformat(),
            message_count=conversation_message_count(db, c.id),
        )
        for c in rows
    ]


@router.get("/stats")
def admin_stats(_: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    n_users = db.scalar(select(func.count()).select_from(User)) or 0
    n_conv = db.scalar(select(func.count()).select_from(Conversation)) or 0
    n_msg = db.scalar(select(func.count()).select_from(Message)) or 0
    topics = (
        db.execute(
            select(Conversation.title, func.count().label("cnt"))
            .group_by(Conversation.title)
            .order_by(func.count().desc())
            .limit(10)
        )
        .all()
    )
    return {
        "users_total": n_users,
        "conversations_total": n_conv,
        "messages_total": n_msg,
        "popular_titles": [{"title": t, "count": c} for t, c in topics],
    }


class LLMSwitchBody(BaseModel):
    provider: str | None = None
    ollama_model: str | None = None
    clear_runtime: bool = False


class LLMTestBody(BaseModel):
    prompt: str = "Скажи коротко по-русски: привет."


@router.get("/llm/status")
def admin_llm_status(_: User = Depends(get_current_admin)):
    s = get_settings()
    snap = runtime_snapshot()
    prov = get_effective_provider()
    ollama_model = get_effective_ollama_model()
    return {
        "effective_provider": prov,
        "provider_override": snap["provider_override"],
        "env_llm_provider": s.llm_provider,
        "ollama_base_url": s.ollama_base_url,
        "ollama_model": ollama_model,
        "ollama_model_override": snap["ollama_model_override"],
        "ollama_reachable": ping_ollama(),
        "openrouter_configured": bool(os.getenv("OPENROUTER_API_KEY", "").strip()),
    }


@router.post("/llm/switch")
def admin_llm_switch(body: LLMSwitchBody, _: User = Depends(get_current_admin)):
    if body.clear_runtime:
        set_runtime_provider(None)
        set_runtime_ollama_model(None)
    else:
        if not (body.provider or "").strip():
            raise HTTPException(status_code=400, detail="provider is required unless clear_runtime=true")
        try:
            set_runtime_provider(body.provider)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
        if "ollama_model" in body.model_fields_set:
            set_runtime_ollama_model(body.ollama_model)
    return {
        "ok": True,
        "effective_provider": get_effective_provider(),
        "ollama_model": get_effective_ollama_model(),
    }


@router.post("/llm/test")
async def admin_llm_test(body: LLMTestBody, _: User = Depends(get_current_admin)):
    mr = ModelRouter()
    model = mr.select_model("question")
    messages = [{"role": "user", "content": body.prompt}]
    reply = await chat_completion_global_async(
        messages, model=model, temperature=0.5, max_tokens=256
    )
    return {"reply": reply, "model": model, "effective_provider": get_effective_provider()}
