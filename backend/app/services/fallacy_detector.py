"""
Анализ ответа: эвристика глубины + LLM (ошибки + оценка глубины).
"""

from __future__ import annotations

import json
from typing import Any

from app.services.model_router import ModelRouter
from app.services.pedagogy_heuristics import heuristic_depth

FALLACY_TYPES = frozenset(
    {
        "none",
        "straw_man",
        "ad_hominem",
        "false_dilemma",
        "appeal_to_authority",
        "hasty_generalization",
    }
)

SYSTEM_PROMPT = """Ты педагог-логик. Ответь СТРОГО одним JSON-объектом без markdown.
Поля:
- "has_fallacy": boolean — есть ли заметная логическая ошибка в ответе ученика относительно вопроса тьютора.
- "fallacy_type": одно из: "none", "straw_man", "ad_hominem", "false_dilemma", "appeal_to_authority", "hasty_generalization"
- "fallacy_description": кратко по-русски для ученика (1–2 предложения), или ""
- "suggestion": мягкий совет как исправить мысль, или ""
- "depth_score": число 0.0–1.0 — насколько ответ глубокий (аргументы, причины, связность), 0 = поверхностный.

Если сомневаешься в ошибке — has_fallacy=false."""
def _normalize_fallacy_type(raw: str) -> str:
    t = (raw or "none").strip().lower()
    return t if t in FALLACY_TYPES else "none"


async def analyze_response(
    router: ModelRouter,
    user_response: str,
    question: str,
    dialog_history: str,
) -> dict[str, Any]:
    """
    Возвращает:
      has_fallacy, fallacy_type, fallacy_description, suggestion,
      depth_heuristic, depth_llm, depth_combined
    """
    h = heuristic_depth(user_response)
    user_prompt = f"""Последний вопрос тьютора:
{question or "(нет)"}

Краткий контекст (последние реплики):
{dialog_history or "(пусто)"}

Ответ ученика:
{user_response}
"""
    raw = await router.call_pedagogy_llm(SYSTEM_PROMPT, user_prompt)
    try:
        data = router.parse_json_object(raw)
    except ValueError:
        data = {}

    depth_llm = data.get("depth_score")
    try:
        depth_llm_f = float(depth_llm)
    except (TypeError, ValueError):
        depth_llm_f = 0.5
    depth_llm_f = max(0.0, min(1.0, depth_llm_f))

    has_fallacy = bool(data.get("has_fallacy"))
    ft = _normalize_fallacy_type(str(data.get("fallacy_type") or "none"))
    if ft == "none":
        has_fallacy = False
    desc = str(data.get("fallacy_description") or "").strip()
    sug = str(data.get("suggestion") or "").strip()

    combined = (h + depth_llm_f) / 2.0

    return {
        "has_fallacy": has_fallacy,
        "fallacy_type": ft if has_fallacy else "none",
        "fallacy_description": desc if has_fallacy else "",
        "suggestion": sug if has_fallacy else "",
        "depth_heuristic": h,
        "depth_llm": depth_llm_f,
        "depth_combined": combined,
    }
