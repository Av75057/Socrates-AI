from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.security import create_access_token, hash_password, verify_password
from app.db.models import GamificationProgress, User, UserSettings
from app.services.learning_service import ensure_learning_rows
from app.db.session import get_db
from app.limiter_instance import limiter

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterBody(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)
    full_name: str | None = Field(None, max_length=255)


class LoginBody(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


def _user_public(u: User) -> dict:
    s = get_settings()
    avatar_url = None
    if u.avatar_path:
        base = (s.public_api_url or "").strip().rstrip("/")
        avatar_url = f"{base}/{u.avatar_path.lstrip('/')}" if base else f"/{u.avatar_path.lstrip('/')}"
    return {
        "id": u.id,
        "email": u.email,
        "full_name": u.full_name,
        "avatar_url": avatar_url,
        "role": u.role,
        "is_active": u.is_active,
    }


@router.post("/register", response_model=TokenResponse)
def register(body: RegisterBody, db: Session = Depends(get_db)):
    exists = db.execute(select(User).where(User.email == body.email.lower())).scalar_one_or_none()
    if exists:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    u = User(
        email=body.email.lower(),
        hashed_password=hash_password(body.password),
        full_name=body.full_name,
        role="user",
        is_active=True,
    )
    db.add(u)
    db.flush()
    db.add(
        UserSettings(
            user_id=u.id,
            tutor_mode="friendly",
            theme="dark",
            notifications_enabled=True,
            has_seen_onboarding=False,
            show_typing_indicator=True,
            russian_only=True,
        )
    )
    db.add(
        GamificationProgress(
            user_id=u.id,
            wisdom_points=0,
            level=1,
            achievements=[],
            streak_days=0,
            last_daily_challenge_date=None,
            extra_state=None,
        )
    )
    ensure_learning_rows(db, u.id)
    db.commit()
    db.refresh(u)
    token = create_access_token(str(u.id))
    return TokenResponse(access_token=token, user=_user_public(u))


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
def login(request: Request, body: LoginBody, db: Session = Depends(get_db)):
    u = db.execute(select(User).where(User.email == body.email.lower())).scalar_one_or_none()
    if u is None or not verify_password(body.password, u.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if not u.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")
    token = create_access_token(str(u.id))
    return TokenResponse(access_token=token, user=_user_public(u))
