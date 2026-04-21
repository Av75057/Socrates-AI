"""Первый вопрос тьютора при создании диалога (LLM + профиль из БД)."""

from __future__ import annotations

import logging
import re

from starlette.concurrency import run_in_threadpool

from app.config import get_settings
from app.db.models import UserPedagogy
from app.db.session import SessionLocal
from app.services.learning_service import (
    build_persistent_profile_for_prompt,
    ensure_user_pedagogy,
    ensure_user_skills,
)
from app.services.model_router import ModelRouter
from app.services.prompt_builder import build_prompt
from app.services.user_settings_db import build_model_router_for_user, get_tutor_mode

log = logging.getLogger(__name__)

_BAD_OPENING = re.compile(r"^\[(?:OpenRouter|LLM)\]")


def _load_opening_context(user_id: int, topic: str) -> tuple[str, str, int, str]:
    with SessionLocal() as db:
        ensure_user_pedagogy(db, user_id)
        ensure_user_skills(db, user_id)
        tm = get_tutor_mode(db, user_id)
        ped = db.get(UserPedagogy, user_id)
        diff = max(1, min(5, int(ped.current_difficulty or 1))) if ped else 1
        prof = build_persistent_profile_for_prompt(db, user_id)
    topic_clean = (topic or "").strip() or "Новый диалог"
    return tm, prof, diff, topic_clean


async def generate_conversation_opening_message(user_id: int, topic: str) -> str | None:
    if not get_settings().conversation_opening_enabled:
        return None
    try:
        tm, prof, diff, topic_clean = await run_in_threadpool(_load_opening_context, user_id, topic)
    except Exception:
        log.exception("opening context load failed user_id=%s", user_id)
        return None

    prompt = build_prompt(
        "question",
        topic_clean,
        [],
        user_type="lazy",
        memory_block="",
        tutor_mode=tm,
        difficulty_level=diff,
        fallacy_instruction="",
        persistent_profile=prof,
    )
    user_line = (
        "Диалог только начался, ученик ещё не писал. "
        f"Тема: «{topic_clean}». "
        "Дай один первый сократовский вопрос по теме (1–2 коротких предложения), строго на русском языке. "
        "Без эмодзи и без декоративных символов. "
        "Без формального приветствия; не копируй дословно длинное название темы."
    )
    try:
        def _router() -> ModelRouter:
            with SessionLocal() as db:
                return build_model_router_for_user(db, user_id)

        router = await run_in_threadpool(_router)
        text = (await router.generate(prompt, user_line, "question")).strip()
    except Exception:
        log.exception("opening LLM failed user_id=%s", user_id)
        return None
    if not text or _BAD_OPENING.match(text):
        return None
    return text
