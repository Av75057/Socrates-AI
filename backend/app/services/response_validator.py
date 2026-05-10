"""Validates LLM output before it reaches the user (pipeline step after model)."""

import re

_HARSH = re.compile(
    r"\b(неправильн|неверн|ты\s+ошиб|ты\s+не\s+прав|ты\s+ошибся|ты\s+ошиблась)\b",
    re.IGNORECASE,
)
_TRAILING_TECH_ARTIFACTS = (
    re.compile(r"(?:\s|^)(?:_[a-z]+(?:_[a-z0-9]+)*_\d+)\s*$", re.IGNORECASE),
    re.compile(r"(?:\s|^)(?:_[a-z]+(?:_[a-z0-9]+)*)\s*$", re.IGNORECASE),
    re.compile(r"(?:\s|^)(?:<\|[^|]+?\|>)\s*$", re.IGNORECASE),
)
_INLINE_TECH_ARTIFACTS = (
    re.compile(r"<\|[^|]+?\|>", re.IGNORECASE),
    re.compile(r"(?<!\w)_(?:pairs|index|template|artifact|token|marker)(?:_[a-z0-9]+)*_?\d*(?!\w)", re.IGNORECASE),
)


def normalize_response_text(response: str) -> str:
    text = str(response or "")
    text = text.replace("\\cdot", "×").replace("\\times", "×")
    for pattern in _INLINE_TECH_ARTIFACTS:
        text = pattern.sub("", text)
    previous = None
    while previous != text:
        previous = text
        for pattern in _TRAILING_TECH_ARTIFACTS:
            text = pattern.sub("", text)
        text = re.sub(r"[ \t]+\n", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def validate_response(response: str, mode: str) -> bool:
    if len(response) > 500:
        return False
    if mode == "question" and "?" not in response:
        return False
    if _HARSH.search(response):
        return False
    return True
