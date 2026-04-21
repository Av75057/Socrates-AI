"""
Долговременное обучение: навыки (user_skills), педагогика (user_pedagogy), контекст для промпта.

Эвристики навыков — см. SKILL_HEURISTICS и FALLACY_TO_SKILL_PENALTY.
LLM для logical_consistency — редко (каждые N ответов), ошибки не пробрасываются наружу.
"""

from __future__ import annotations

import logging
import os
import re
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.services.llm.global_call import chat_completion_global_sync
from app.services.llm.runtime import get_effective_ollama_model, get_effective_provider
from app.db.models import Conversation, Skill, User, UserPedagogy, UserSkill
from app.services.conversation_db import display_title_for_conversation

log = logging.getLogger(__name__)

TOPIC_HINT_BY_SKILL = {
    "avoid_straw_man": "Логические ошибки: искажение аргументов (соломенное чучело)",
    "avoid_ad_hominem": "Аргументация без перехода на личности",
    "use_counterexample": "Контрпримеры и проверка идей",
    "ask_clarifying": "Уточняющие вопросы и критическое мышление",
    "structure_argument": "Структура аргумента: тезис, основание, вывод",
    "logical_consistency": "Внутренняя согласованность рассуждения",
}

_RE_COUNTEREXAMPLE = re.compile(
    r"(например|представь|представим|если\s+.+\s+то|контрпример)",
    re.IGNORECASE | re.DOTALL,
)
_RE_STRUCTURE = re.compile(
    r"(потому\s+что|следовательно|таким\s+образом|поэтому|значит,)",
    re.IGNORECASE,
)
_RE_CLARIFY_START = re.compile(
    r"^\s*(почему|как|что|где|когда|зачем|какой|какая|какие|или\s+нет)\b",
    re.IGNORECASE,
)


def ensure_user_pedagogy(db: Session, user_id: int) -> UserPedagogy:
    row = db.get(UserPedagogy, user_id)
    if row is None:
        row = UserPedagogy(
            user_id=user_id,
            current_difficulty=1,
            total_deep_responses=0,
            total_shallow_responses=0,
            fallacy_counts={},
            last_active_at=datetime.now(timezone.utc),
            logic_check_counter=0,
        )
        db.add(row)
        db.flush()
    elif row.fallacy_counts is None:
        row.fallacy_counts = {}
    return row


def ensure_user_skills(db: Session, user_id: int) -> None:
    skill_ids = db.execute(select(Skill.skill_id)).scalars().all()
    existing = set(
        db.execute(select(UserSkill.skill_id).where(UserSkill.user_id == user_id)).scalars().all()
    )
    now = datetime.now(timezone.utc)
    for sid in skill_ids:
        if sid not in existing:
            db.add(UserSkill(user_id=user_id, skill_id=sid, level=0, last_updated=now))
    if skill_ids:
        db.flush()


def ensure_learning_rows(db: Session, user_id: int) -> None:
    ensure_user_pedagogy(db, user_id)
    ensure_user_skills(db, user_id)


def hydrate_session_pedagogy_from_db(db: Session, user_id: int, state: Any) -> None:
    """Подмешать в Redis-состояние сложность и частые ошибки из БД."""
    row = db.get(UserPedagogy, user_id)
    if row is None:
        return
    state.difficulty_level = max(1, min(5, int(row.current_difficulty or 1)))
    counts = row.fallacy_counts if isinstance(row.fallacy_counts, dict) else {}

    def _cnt(v: Any) -> int:
        try:
            return int(v)
        except (TypeError, ValueError):
            return 0

    for ft, n in sorted(counts.items(), key=lambda x: -_cnt(x[1]))[:10]:
        if ft and str(ft) != "none" and _cnt(n) > 0 and ft not in state.common_fallacies:
            state.common_fallacies.append(str(ft))
    state.common_fallacies = state.common_fallacies[-15:]


def _skill_delta_for_difficulty(difficulty: int) -> int:
    return max(1, min(3, 1 + (difficulty // 2)))


def _logical_consistency_sync(user_text: str) -> bool | None:
    """
    True — противоречий не видно (повышаем навык), False — есть, None — сбой/пропуск.
    """
    s = get_settings()
    if not s.skill_update_enabled:
        return None
    if get_effective_provider() == "openrouter" and not os.getenv("OPENROUTER_API_KEY", "").strip():
        return None
    model = get_effective_ollama_model() if get_effective_provider() == "ollama" else s.logical_consistency_model
    system = (
        "Ответь одним словом: ДА — если в тексте ученика есть явное логическое противоречие "
        "(утверждение A и не-A в одной мысли), НЕТ — если явного противоречия нет. Только ДА или НЕТ."
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user_text[:4000]},
    ]
    try:
        content = chat_completion_global_sync(
            messages,
            model=model,
            temperature=0.0,
            max_tokens=8,
            timeout_s=20.0,
        )
        low = content.strip().lower()
        if low.startswith("да"):
            return False
        if low.startswith("нет"):
            return True
    except Exception:
        log.debug("logical_consistency LLM failed", exc_info=True)
    return None


def _adjust_skill(db: Session, user_id: int, skill_id: str, delta: int) -> None:
    row = db.execute(
        select(UserSkill).where(UserSkill.user_id == user_id, UserSkill.skill_id == skill_id)
    ).scalar_one_or_none()
    if row is None:
        return
    row.level = max(0, min(100, int(row.level) + delta))
    row.last_updated = datetime.now(timezone.utc)


def update_user_learning_progress_sync(
    user_id: int,
    user_text: str,
    analysis: dict[str, Any] | None,
    session_difficulty_after_turn: int,
) -> None:
    if not get_settings().skill_update_enabled:
        return
    if not user_text.strip() or analysis is None:
        return
    from app.db.session import SessionLocal

    depth = float(analysis.get("depth_combined") or analysis.get("depth_heuristic") or 0.0)
    has_f = bool(analysis.get("has_fallacy"))
    ftype = str(analysis.get("fallacy_type") or "none").strip().lower()

    try:
        with SessionLocal() as db:
            ped = ensure_user_pedagogy(db, user_id)
            ensure_user_skills(db, user_id)

            if depth > 0.6:
                ped.total_deep_responses += 1
            else:
                ped.total_shallow_responses += 1

            if has_f and ftype and ftype != "none":
                fc = dict(ped.fallacy_counts or {})
                fc[ftype] = int(fc.get(ftype, 0)) + 1
                ped.fallacy_counts = fc

            inc = _skill_delta_for_difficulty(session_difficulty_after_turn)

            if has_f and ftype == "straw_man":
                _adjust_skill(db, user_id, "avoid_straw_man", -3)
            else:
                _adjust_skill(db, user_id, "avoid_straw_man", inc)

            if has_f and ftype == "ad_hominem":
                _adjust_skill(db, user_id, "avoid_ad_hominem", -3)
            else:
                _adjust_skill(db, user_id, "avoid_ad_hominem", inc)

            low = user_text.lower()
            if _RE_COUNTEREXAMPLE.search(user_text):
                _adjust_skill(db, user_id, "use_counterexample", inc)
            if "?" in user_text or _RE_CLARIFY_START.match(user_text.strip()):
                _adjust_skill(db, user_id, "ask_clarifying", inc)
            if _RE_STRUCTURE.search(user_text):
                _adjust_skill(db, user_id, "structure_argument", inc)

            n = get_settings().logical_consistency_every_n
            if n > 0:
                ped.logic_check_counter += 1
                if ped.logic_check_counter >= n:
                    ped.logic_check_counter = 0
                    lc = _logical_consistency_sync(user_text)
                    if lc is True:
                        _adjust_skill(db, user_id, "logical_consistency", inc)
                    elif lc is False:
                        _adjust_skill(db, user_id, "logical_consistency", -2)

            t = ped.total_deep_responses + ped.total_shallow_responses
            ratio_d = 1
            if t > 0:
                ratio_d = max(1, min(5, round((ped.total_deep_responses / t) * 5)))
            blended = max(1, min(5, round((ratio_d + session_difficulty_after_turn) / 2)))
            ped.current_difficulty = blended
            ped.last_active_at = datetime.now(timezone.utc)
            db.commit()
    except Exception:
        log.exception("update_user_learning_progress failed user_id=%s", user_id)


def build_persistent_profile_for_prompt(db: Session, user_id: int) -> str:
    ped = db.get(UserPedagogy, user_id)
    if ped is None:
        return ""
    skills = (
        db.execute(
            select(UserSkill, Skill)
            .join(Skill, Skill.skill_id == UserSkill.skill_id)
            .where(UserSkill.user_id == user_id)
        )
        .all()
    )
    lines: list[str] = []
    lines.append(
        f"Текущая целевая сложность диалога (из профиля ученика): {ped.current_difficulty}/5. "
        "Адаптируй глубину вопросов под этот уровень."
    )
    fc = ped.fallacy_counts if isinstance(ped.fallacy_counts, dict) else {}
    top_f = sorted(fc.items(), key=lambda x: -int(x[1] or 0))[:3]
    if top_f:
        parts = [f"{k} (≈{v} раз)" for k, v in top_f if k and k != "none"]
        if parts:
            lines.append(
                "Частые логические слабости ученика по истории: "
                + ", ".join(parts)
                + ". Мягко обращай внимание на эти типы ошибок, не унижая."
            )
    if skills:
        skill_lines = [f"— {s[1].name}: {s[0].level}/100" for s in sorted(skills, key=lambda x: -x[0].level)[:6]]
        lines.append("Уровни навыков ученика:\n" + "\n".join(skill_lines))
    return "\n\n".join(lines).strip()


def get_user_skills_summary(db: Session, user_id: int) -> list[dict[str, Any]]:
    ensure_user_pedagogy(db, user_id)
    ensure_user_skills(db, user_id)
    rows = (
        db.execute(
            select(UserSkill, Skill)
            .join(Skill, Skill.skill_id == UserSkill.skill_id)
            .where(UserSkill.user_id == user_id)
            .order_by(Skill.skill_id)
        )
        .all()
    )
    out = []
    for us, sk in rows:
        out.append(
            {
                "skill_id": sk.skill_id,
                "name": sk.name,
                "description": sk.description or "",
                "level": us.level,
            }
        )
    return out


def get_user_pedagogy_public(db: Session, user_id: int) -> dict[str, Any]:
    ped = ensure_user_pedagogy(db, user_id)
    return {
        "current_difficulty": ped.current_difficulty,
        "total_deep_responses": ped.total_deep_responses,
        "total_shallow_responses": ped.total_shallow_responses,
        "fallacy_counts": dict(ped.fallacy_counts or {}),
        "last_active_at": ped.last_active_at.isoformat(),
    }


def get_recommendation(db: Session, user_id: int) -> dict[str, Any]:
    ensure_user_pedagogy(db, user_id)
    ensure_user_skills(db, user_id)
    conv = (
        db.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.last_updated_at.desc())
            .limit(1)
        )
        .scalars()
        .first()
    )
    last_c = None
    if conv:
        last_c = {
            "id": conv.id,
            "title": display_title_for_conversation(db, conv),
            "last_updated": conv.last_updated_at.date().isoformat(),
        }
    weak = (
        db.execute(
            select(UserSkill.skill_id)
            .where(UserSkill.user_id == user_id)
            .order_by(UserSkill.level.asc())
            .limit(3)
        )
        .scalars()
        .all()
    )
    weak_list = list(weak)
    topic = "Логика и аргументация"
    if weak_list:
        topic = TOPIC_HINT_BY_SKILL.get(weak_list[0], topic)
    # Короткое персонализированное сообщение
    parts_msg = []
    if weak_list:
        labels = []
        for sid in weak_list[:2]:
            sk = db.execute(select(Skill).where(Skill.skill_id == sid)).scalar_one_or_none()
            labels.append(sk.name if sk else sid)
        parts_msg.append(f"Стоит потренировать: {', '.join(labels)}.")
    parts_msg.append(f"Идея для темы: «{topic}».")
    message = " ".join(parts_msg)
    return {
        "last_conversation": last_c,
        "weak_skills": weak_list,
        "recommended_topic": topic,
        "message": message,
    }


def reset_user_learning(db: Session, user_id: int) -> None:
    ped = db.get(UserPedagogy, user_id)
    if ped:
        ped.current_difficulty = 1
        ped.total_deep_responses = 0
        ped.total_shallow_responses = 0
        ped.fallacy_counts = {}
        ped.logic_check_counter = 0
        ped.last_active_at = datetime.now(timezone.utc)
    for us in db.execute(select(UserSkill).where(UserSkill.user_id == user_id)).scalars().all():
        us.level = 0
        us.last_updated = datetime.now(timezone.utc)
    db.commit()
