from __future__ import annotations

import logging
from typing import Any

from app.db.session import SessionLocal
from app.logging_setup import log_event
from app.services.adaptive_difficulty import get_skill_id_for_topic_id
from app.services.fallacy_detector import analyze_response
from app.services.prompt_builder import _history_to_text

log = logging.getLogger(__name__)


def _last_assistant_question(history: list[dict[str, Any]]) -> str:
    for item in reversed(history):
        if isinstance(item, dict) and item.get("role") == "assistant":
            return str(item.get("content") or "").strip()
    return ""


def _score_analysis(analysis: dict[str, Any]) -> float:
    depth = float(analysis.get("depth_combined") or analysis.get("depth_heuristic") or 0.0)
    has_fallacy = bool(analysis.get("has_fallacy"))
    if not has_fallacy and depth >= 0.75:
        return 1.0
    if not has_fallacy and depth >= 0.55:
        return 0.7
    if depth >= 0.3:
        return 0.4
    return 0.0


def _detected_skills(context: Any) -> list[str]:
    topic_id = getattr(context.state, "topic_id", None)
    if topic_id is None:
        return []
    with SessionLocal() as db:
        skill_id = get_skill_id_for_topic_id(db, topic_id)
    return [skill_id] if skill_id else []


class AnswerAnalyzer:
    async def analyze(self, context: Any) -> dict[str, Any] | None:
        if context.cheat or context.idle_turn or context.body.action != "none" or not context.msg_stripped:
            return None
        analysis = await analyze_response(
            context.router,
            context.msg_stripped,
            _last_assistant_question(context.state.history),
            _history_to_text(context.state.history, max_messages=10),
        )
        if analysis.get("has_fallacy"):
            fallacy_type = str(analysis.get("fallacy_type") or "")
            if fallacy_type and fallacy_type != "none" and fallacy_type not in context.pedagogy_state.common_fallacies:
                context.pedagogy_state.common_fallacies.append(fallacy_type)
                context.pedagogy_state.common_fallacies = context.pedagogy_state.common_fallacies[-15:]
        analysis["score"] = _score_analysis(analysis)
        analysis["detected_skills"] = _detected_skills(context)
        log_event(log, logging.DEBUG, "Answer analyzed", phase=context.state.phase)
        return analysis
