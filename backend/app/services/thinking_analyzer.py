"""Эвристический анализ стиля мышления по тексту пользователя (MVP без LLM)."""

from __future__ import annotations

from typing import Any

# Оценки 0..2 для усреднения по последним репликам
_LOW_CONF = (
    "наверное",
    "может быть",
    "не уверен",
    "не уверена",
    "кажется",
    "вроде бы",
    "хз",
    "не знаю точно",
    "наверняка не",
)

_LOGIC_GOOD = (
    "потому что",
    "так как",
    "следовательно",
    "значит",
    "если ",
    "то ",
    "причин",
    "следств",
    "отсюда",
)


def should_analyze_user_message(message: str) -> bool:
    raw = (message or "").strip()
    if len(raw) < 2:
        return False
    if raw.startswith("(") and raw.endswith(")"):
        return False
    if "запрошена подсказка" in raw.lower() or "сдаюсь" in raw.lower()[:40]:
        return False
    return True


def analyze_scores(message: str) -> dict[str, int]:
    t = (message or "").strip()
    low = t.lower()

    if len(t) < 10:
        d = 0
    elif len(t) < 50:
        d = 1
    else:
        d = 2

    if any(x in low for x in _LOW_CONF):
        c = 0
    elif "?" in t and len(t) < 40:
        c = 1
    else:
        c = 2

    if any(x in low for x in _LOGIC_GOOD):
        l = 2
    elif len(t) >= 25:
        l = 1
    else:
        l = 0

    return {"d": d, "l": l, "c": c}


def _avg(scores: list[dict[str, int]], key: str) -> float:
    if not scores:
        return 1.0
    return sum(s.get(key, 1) for s in scores) / len(scores)


def _depth_label(avg: float) -> str:
    if avg < 0.66:
        return "low"
    if avg < 1.55:
        return "medium"
    return "high"


def _logic_label(avg: float) -> str:
    if avg < 0.66:
        return "weak"
    if avg < 1.55:
        return "partial"
    return "strong"


def _confidence_label(avg: float) -> str:
    if avg < 0.66:
        return "low"
    if avg < 1.55:
        return "medium"
    return "high"


def aggregate_profile(scores: list[dict[str, int]]) -> dict[str, Any]:
    if not scores:
        return {
            "depth": "medium",
            "logic": "partial",
            "confidence": "medium",
            "samples": 0,
        }
    return {
        "depth": _depth_label(_avg(scores, "d")),
        "logic": _logic_label(_avg(scores, "l")),
        "confidence": _confidence_label(_avg(scores, "c")),
        "samples": len(scores),
    }


def get_effective_profile(
    history: list[dict[str, int]],
    current_message: str,
) -> dict[str, Any]:
    """Профиль с учётом текущего сообщения (для промпта в этом же ходе)."""
    scores = list(history)
    if should_analyze_user_message(current_message):
        scores.append(analyze_scores(current_message))
    scores = scores[-5:]
    return aggregate_profile(scores)


def format_thinking_for_prompt(profile: dict[str, Any]) -> str:
    """Короткие инструкции для модели."""
    if not profile or profile.get("samples", 0) == 0:
        return ""

    d = profile.get("depth")
    l = profile.get("logic")
    c = profile.get("confidence")

    parts = [
        "Когнитивный профиль ученика (не озвучивай как диагноз и не перечисляй вслух):",
    ]
    if l in ("weak", "partial"):
        parts.append(
            "- Слабее выстроена причинно-следственная связь: чаще проси одним коротким шагом «почему так» / «что из этого следует»."
        )
    if c == "low":
        parts.append(
            "- Низкая уверенность в формулировках: поддержи («ты на правильном пути», «это нормально сомневаться»), без панибратства."
        )
    if d == "low":
        parts.append(
            "- Ответы обычно очень краткие: мягко попроси чуть конкретики или одного примера («давай чуть подробнее»)."
        )
    if d == "high" and l == "strong":
        parts.append(
            "- Видны развёрнутые рассуждения: можно аккуратно углубить или дать контрпример."
        )

    parts.append("Максимум одна такая реакция за ответ, естественно вплети в вопрос.")
    return "\n".join(parts)
