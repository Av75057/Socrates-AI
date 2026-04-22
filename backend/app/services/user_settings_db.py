from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import UserSettings
from app.services.model_router import ModelRouter


def get_tutor_mode(db: Session, user_id: int) -> str:
    row = db.execute(select(UserSettings).where(UserSettings.user_id == user_id)).scalar_one_or_none()
    return row.tutor_mode if row else "friendly"


def get_russian_only(db: Session, user_id: int) -> bool:
    row = db.execute(select(UserSettings).where(UserSettings.user_id == user_id)).scalar_one_or_none()
    return bool(row.russian_only) if row else True


def build_model_router_for_user(db: Session, user_id: int) -> ModelRouter:
    """
    Если в настройках заданы llm_base_url и llm_model_name — используем локальный OpenAI-совместимый endpoint.
    Иначе — глобальный OpenRouter из переменных окружения.
    """
    row = db.execute(select(UserSettings).where(UserSettings.user_id == user_id)).scalar_one_or_none()
    if row is None:
        return ModelRouter()

    base = (row.llm_base_url or "").strip()
    model = (row.llm_model_name or "").strip()
    if not base or not model:
        return ModelRouter()

    key = (row.llm_api_key or "").strip()
    if not key:
        key = "sk-no-key-required"

    return ModelRouter(
        api_key=key,
        api_url=base,
        custom_model_name=model,
        use_openrouter_headers=False,
    )
