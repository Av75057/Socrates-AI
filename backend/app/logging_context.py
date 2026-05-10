from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar, Token
from typing import Any, Iterator

_log_context: ContextVar[dict[str, Any]] = ContextVar("log_context", default={})


def get_log_context() -> dict[str, Any]:
    return dict(_log_context.get())


def bind_log_context(**fields: Any) -> Token:
    context = get_log_context()
    for key, value in fields.items():
        if value is not None:
            context[key] = value
    return _log_context.set(context)


def reset_log_context(token: Token) -> None:
    _log_context.reset(token)


@contextmanager
def log_context(**fields: Any) -> Iterator[None]:
    token = bind_log_context(**fields)
    try:
        yield
    finally:
        reset_log_context(token)
