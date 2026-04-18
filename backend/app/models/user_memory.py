"""Долговременная память о пользователе (Redis), отдельно от сессии чата."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class UserMemory:
    topics: list[str] = field(default_factory=list)
    mistakes: list[dict[str, str]] = field(default_factory=list)
    progress: dict[str, str] = field(default_factory=dict)
    user_type: str = "lazy"

    def to_dict(self) -> dict[str, Any]:
        return {
            "topics": list(self.topics),
            "mistakes": list(self.mistakes),
            "progress": dict(self.progress),
            "user_type": self.user_type,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> UserMemory:
        if not data or not isinstance(data, dict):
            return cls()
        topics = data.get("topics") or []
        mistakes = data.get("mistakes") or []
        progress = data.get("progress") or {}
        ut = str(data.get("user_type", "lazy") or "lazy").lower()
        if ut not in ("lazy", "anxious", "thinker"):
            ut = "lazy"
        return cls(
            topics=[str(t) for t in topics if t][:50],
            mistakes=[dict(m) for m in mistakes if isinstance(m, dict)][:40],
            progress={str(k): str(v) for k, v in progress.items() if k} if isinstance(progress, dict) else {},
            user_type=ut,
        )
