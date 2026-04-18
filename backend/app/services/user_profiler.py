"""Определение типа ученика для адаптации тона и UI (lazy / anxious / thinker)."""

from __future__ import annotations

UserType = str  # "lazy" | "anxious" | "thinker"

_LAZY_MARKERS = (
    "не знаю",
    "хз",
    "без понятия",
    "лень",
    "не хочу думать",
)

_ANXIOUS_MARKERS = (
    "не понимаю",
    "туплю",
    "сложно",
    "я тупой",
    "я тупая",
    "боюсь ошиб",
    "страшно ошиб",
    "не уверен",
    "не уверена",
    "запутался",
    "запуталась",
)

_LAZY_SHORT = frozenset(
    {
        "да",
        "нет",
        "ок",
        "окей",
        "угу",
        "ага",
        "неа",
        "ну",
        "э",
    }
)


def detect_user_type(message: str, current: UserType | None) -> UserType:
    """Эвристика по последнему сообщению; при сомнении сохраняем прежний тип."""
    raw = (message or "").strip()
    base = (current or "lazy").lower()
    if base not in ("lazy", "anxious", "thinker"):
        base = "lazy"

    if not raw:
        return base

    low = raw.lower()

    if len(raw) >= 50:
        return "thinker"

    if any(x in low for x in _ANXIOUS_MARKERS):
        return "anxious"

    if any(x in low for x in _LAZY_MARKERS):
        return "lazy"

    if len(raw) <= 5 and low in _LAZY_SHORT:
        return "lazy"

    if len(raw) < 15 and base == "thinker" and not any(x in low for x in _ANXIOUS_MARKERS):
        return base

    return base
