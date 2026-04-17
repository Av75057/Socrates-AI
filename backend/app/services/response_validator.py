"""Validates LLM output before it reaches the user (pipeline step after model)."""


def validate_response(response: str, mode: str) -> bool:
    if len(response) > 500:
        return False
    if mode == "question" and "?" not in response:
        return False
    return True
