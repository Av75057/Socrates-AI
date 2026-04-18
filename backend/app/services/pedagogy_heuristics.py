"""Эвристики глубины и текст инструкции при логической ошибке (без LLM)."""

from __future__ import annotations

from typing import Any


def heuristic_depth(user_response: str) -> float:
    t = (user_response or "").strip()
    if not t:
        return 0.0
    score = 0.15
    if len(t) > 100:
        score += 0.2
    low = t.lower()
    links = (
        "потому что",
        "следовательно",
        "например",
        "во-первых",
        "во-вторых",
        "так как",
        "поэтому",
    )
    if any(x in low for x in links):
        score += 0.3
    if any(x in low for x in ("ты сказал", "ты спросил", "ранее ты", "как ты ответил")):
        score += 0.2
    return min(1.0, score)


def build_fallacy_instruction(tutor_mode: str, analysis: dict[str, Any]) -> str:
    if not analysis.get("has_fallacy"):
        return ""
    m = (tutor_mode or "friendly").strip().lower()
    ft = analysis.get("fallacy_type") or "ошибка"
    desc = (analysis.get("fallacy_description") or "").strip()
    sug = (analysis.get("suggestion") or "").strip()
    if m == "strict":
        return (
            f"У ученика, вероятно, логическая ошибка типа «{ft}»: {desc} "
            f"Сначала коротко и по делу укажи на это (без оскорблений). "
            f"Не выдавай готовый ответ. Затем один жёсткий уточняющий вопрос. "
            f"Совет: {sug}"
        ).strip()
    if m == "provocateur":
        return (
            f"Найди слабое место в позиции ученика (тип «{ft}»): {desc} "
            f"Провокационно, но без перехода на личность; затем каверзный вопрос. "
            f"Намёк на исправление: {sug}"
        ).strip()
    return (
        f"Мягко и поддерживая укажи на возможную логическую ошибку («{ft}»): {desc} "
        f"Затем продолжи сократическим вопросом. Напомни ученику: {sug}"
    ).strip()
