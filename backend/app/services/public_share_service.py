"""Анонимизация текста для публичного шаринга диалогов."""

from __future__ import annotations

import re
import secrets


def anonymize_public_text(text: str) -> str:
    if not text:
        return ""
    t = re.sub(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b", "[email скрыт]", text)
    t = re.sub(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b", "[телефон скрыт]", t)
    return t


def make_share_slug() -> str:
    """Короткий уникальный идентификатор для URL."""
    return secrets.token_hex(8)
