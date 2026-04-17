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
    history: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "attempts": self.attempts,
            "frustration": self.frustration,
            "mode": self.mode,
            "topic": self.topic,
            "history": self.history,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TutorState:
        return cls(
            attempts=int(data.get("attempts", 0)),
            frustration=int(data.get("frustration", 0)),
            mode=str(data.get("mode", "question")),
            topic=str(data.get("topic", "")),
            history=list(data.get("history", [])),
        )
