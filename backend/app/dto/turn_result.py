from __future__ import annotations

from dataclasses import dataclass

from app.dto.chat_schema import ChatResponse


@dataclass
class TurnResult:
    response: ChatResponse
    mode: str
    raw_reply: str = ""
    latency_ms: int = 0
