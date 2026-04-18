from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps_auth import get_current_admin
from app.db.models import Conversation, GamificationProgress, Message, User, UserSettings
from app.db.session import get_db
from app.services.conversation_db import conversation_message_count

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
        if body.role not in ("user", "admin"):
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
