from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import UserSettings


def get_tutor_mode(db: Session, user_id: int) -> str:
    row = db.execute(select(UserSettings).where(UserSettings.user_id == user_id)).scalar_one_or_none()
    return row.tutor_mode if row else "friendly"
