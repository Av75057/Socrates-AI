from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Topic, UserSkill
from app.logging_setup import log_event

log = logging.getLogger(__name__)

_ALPHA = 0.7


def get_session_skill_id(topic: Topic | None) -> str | None:
    if topic is None:
        return None
    raw = topic.learning_objectives if isinstance(topic.learning_objectives, list) else []
    for item in raw:
        if not isinstance(item, dict):
            continue
        skill_id = str(item.get("skill_id") or "").strip()
        if skill_id:
            return skill_id
    return None


def get_skill_id_for_topic_id(db: Session, topic_id: int | None) -> str | None:
    if topic_id is None:
        return None
    topic = db.get(Topic, topic_id)
    return get_session_skill_id(topic)


def get_skill_mastery(db: Session, user_id: int, skill_id: str) -> float:
    row = db.execute(
        select(UserSkill).where(UserSkill.user_id == user_id, UserSkill.skill_id == skill_id)
    ).scalar_one_or_none()
    if row is None:
        return 0.0
    level = max(0, min(100, int(row.level or 0)))
    return level / 100.0


def update_skill_mastery(db: Session, user_id: int, skill_id: str, answer_score: float) -> float:
    row = db.execute(
        select(UserSkill).where(UserSkill.user_id == user_id, UserSkill.skill_id == skill_id)
    ).scalar_one_or_none()
    if row is None:
        return 0.0
    current_mastery = max(0.0, min(1.0, (int(row.level or 0) / 100.0)))
    score = max(0.0, min(1.0, float(answer_score)))
    new_mastery = (_ALPHA * current_mastery) + ((1.0 - _ALPHA) * score)
    row.level = max(0, min(100, int(round(new_mastery * 100))))
    log_event(
        log,
        logging.INFO,
        "Adaptive mastery updated",
        user_id=user_id,
        skill_id=skill_id,
        old_level=int(round(current_mastery * 100)),
        new_level=row.level,
        answer_score=score,
    )
    return row.level / 100.0


def get_target_difficulty(mastery: float) -> int:
    value = max(0.0, min(1.0, float(mastery)))
    if value < 0.34:
        return 1
    if value < 0.67:
        return 2
    return 3


def skill_progress_payload(level: int) -> dict[str, Any]:
    normalized = max(0, min(100, int(level or 0)))
    mastery = normalized / 100.0
    return {
        "mastery": round(mastery, 3),
        "adaptive_difficulty": get_target_difficulty(mastery),
    }
