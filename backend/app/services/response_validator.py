"""Validates LLM output before it reaches the user (pipeline step after model)."""

import re

_HARSH = re.compile(
    r"\b(неправильн|неверн|ты\s+ошиб|ты\s+не\s+прав|ты\s+ошибся|ты\s+ошиблась)\b",
    re.IGNORECASE,
)


def validate_response(response: str, mode: str) -> bool:
    if len(response) > 500:
        return False
    if mode == "question" and "?" not in response:
        return False
    if _HARSH.search(response):
        return False
    return True
