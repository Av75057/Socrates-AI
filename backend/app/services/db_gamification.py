"""Синхронизация геймификации Redis → строка gamification_progress."""

from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.db.models import GamificationProgress
from app.models.gamification import UserProgressState, recalc_level


def _max_int_from_extra(ex: dict, key: str, default: int = 0) -> int:
    try:
        return max(0, int(ex.get(key, default)))
    except (TypeError, ValueError):
        return max(0, default)


def _merge_numeric_progress_from_row_extra(state: UserProgressState, row: GamificationProgress) -> None:
    """
    Согласовать числа из колонок таблицы и из extra_state (в т.ч. если validate падал,
    а total_user_turns в словаре есть, а wisdom_points в колонке устарел/ноль).
    """
    ex = row.extra_state if isinstance(row.extra_state, dict) else {}
    try:
        col_wp = int(row.wisdom_points or 0)
    except (TypeError, ValueError):
        col_wp = 0
    state.wisdom_points = max(
        state.wisdom_points,
        col_wp,
        _max_int_from_extra(ex, "wisdom_points"),
    )
    state.total_user_turns = max(state.total_user_turns, _max_int_from_extra(ex, "total_user_turns"))
    state.logic_good_streak = max(state.logic_good_streak, _max_int_from_extra(ex, "logic_good_streak"))
    try:
        col_streak = int(row.streak_days or 0)
    except (TypeError, ValueError):
        col_streak = 0
    state.streak_days = max(state.streak_days, col_streak, _max_int_from_extra(ex, "streak_days"))
    state.challenges_completed_total = max(
        state.challenges_completed_total,
        _max_int_from_extra(ex, "challenges_completed_total"),
    )
    state.level = recalc_level(state.wisdom_points)


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


def user_progress_state_from_row(
    row: GamificationProgress | None,
    *,
    fallback_user_id: str,
) -> UserProgressState | None:
    """Восстановить Redis-состояние из БД при первом заходе после смены session_id / пустом Redis."""
    if row is None:
        return None
    extra = row.extra_state
    s: UserProgressState | None = None
    if isinstance(extra, dict) and extra:
        try:
            s = UserProgressState.model_validate(extra)
            s.user_id = fallback_user_id
        except (ValueError, TypeError):
            s = None
    if s is None:
        ex = extra if isinstance(extra, dict) else {}

        def _ex_int(key: str, default: int = 0) -> int:
            try:
                return int(ex.get(key, default))
            except (TypeError, ValueError):
                return default

        s = UserProgressState(
            user_id=fallback_user_id,
            wisdom_points=row.wisdom_points,
            level=recalc_level(row.wisdom_points),
            achievements=list(row.achievements or []),
            last_daily_challenge_date=row.last_daily_challenge_date,
            streak_days=row.streak_days,
            total_user_turns=max(0, _ex_int("total_user_turns", 0)),
            logic_good_streak=max(0, _ex_int("logic_good_streak", 0)),
            challenges_completed_total=max(0, _ex_int("challenges_completed_total", 0)),
        )
    _merge_numeric_progress_from_row_extra(s, row)
    s.user_id = fallback_user_id
    return s


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
