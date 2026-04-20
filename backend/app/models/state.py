"""Persistent tutor state (Redis-serializable)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TutorState:
    attempts: int = 0
    frustration: int = 0
    mode: str = "question"  # question | hint | explain
    topic: str = ""
    user_type: str = "lazy"  # lazy | anxious | thinker
    history: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "attempts": self.attempts,
            "frustration": self.frustration,
            "mode": self.mode,
            "topic": self.topic,
            "user_type": self.user_type,
            "history": self.history,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TutorState:
        ut = str(data.get("user_type", "lazy") or "lazy").lower()
        if ut not in ("lazy", "anxious", "thinker"):
            ut = "lazy"
        raw_hist = data.get("history", [])
        if raw_hist is None:
            hist: list[dict[str, Any]] = []
        elif not isinstance(raw_hist, list):
            hist = []
        else:
            hist = []
            for h in raw_hist:
                if not isinstance(h, dict):
                    continue
                role = h.get("role")
                if role not in ("user", "assistant"):
                    continue
                hist.append({"role": str(role), "content": str(h.get("content") or "")})
        return cls(
            attempts=int(data.get("attempts", 0)),
            frustration=int(data.get("frustration", 0)),
            mode=str(data.get("mode", "question")),
            topic=str(data.get("topic", "")),
            user_type=ut,
            history=hist,
        )
