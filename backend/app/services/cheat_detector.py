"""Heuristic detection of copy-paste / canned answers."""

from __future__ import annotations

SUSPICIOUS_PHRASES = (
    "это закон",
    "определяется как",
    "является",
)


def is_cheating(text: str) -> bool:
    if len(text) > 250:
        return True
    low = text.lower()
    return any(p in low for p in SUSPICIOUS_PHRASES)


CHEAT_REPLY = (
    "Похоже, это готовый ответ 🙂 Попробуй объяснить своими словами, как будто рассказываешь другу."
)
