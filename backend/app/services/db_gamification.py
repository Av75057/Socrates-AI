"""Синхронизация геймификации Redis → строка gamification_progress."""

from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.db.models import GamificationProgress
from app.models.gamification import UserProgressState


def ensure_gamification_row(db: Session, user_id: int) -> GamificationProgress:
    row = db.get(GamificationProgress, user_id)
    if row is None:
        row = GamificationProgress(
            user_id=user_id,
            wisdom_points=0,
            level=1,
            achievements=[],
            streak_days=0,
            last_daily_challenge_date=None,
            extra_state=None,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


def apply_redis_state_to_db(db: Session, user_id: int, state: UserProgressState) -> None:
    row = ensure_gamification_row(db, user_id)
    row.wisdom_points = state.wisdom_points
    row.level = state.level
    row.achievements = list(state.achievements)
    row.streak_days = state.streak_days
    row.last_daily_challenge_date = state.last_daily_challenge_date
    row.extra_state = state.model_dump(mode="json")
    db.commit()


def gamification_row_to_public(row: GamificationProgress) -> dict:
    return {
        "user_id": str(row.user_id),
        "wisdom_points": row.wisdom_points,
        "level": row.level,
        "achievements": list(row.achievements or []),
        "daily_challenge_completed": False,
        "last_daily_challenge_date": row.last_daily_challenge_date.isoformat()
        if row.last_daily_challenge_date
        else None,
        "streak_days": row.streak_days,
        "total_user_turns": (row.extra_state or {}).get("total_user_turns", 0),
    }
