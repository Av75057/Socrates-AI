from __future__ import annotations

import logging
from typing import Any

from app.logging_setup import log_event
from app.services.fallacy_detector import analyze_response
from app.services.prompt_builder import _history_to_text

log = logging.getLogger(__name__)


def _last_assistant_question(history: list[dict[str, Any]]) -> str:
    for item in reversed(history):
        if isinstance(item, dict) and item.get("role") == "assistant":
            return str(item.get("content") or "").strip()
    return ""


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
        log_event(log, logging.DEBUG, "Answer analyzed", phase=context.state.phase)
        return analysis
