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
    skill_status: dict[str, str] = field(default_factory=dict)  # node_id -> in_progress | completed

    def to_dict(self) -> dict[str, Any]:
        return {
            "topics": list(self.topics),
            "mistakes": list(self.mistakes),
            "progress": dict(self.progress),
            "user_type": self.user_type,
            "skill_status": dict(self.skill_status),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> UserMemory:
        if not data or not isinstance(data, dict):
            return cls()
        topics = data.get("topics") or []
        mistakes = data.get("mistakes") or []
        progress = data.get("progress") or {}
        sk = data.get("skill_status") or {}
        ut = str(data.get("user_type", "lazy") or "lazy").lower()
        if ut not in ("lazy", "anxious", "thinker"):
            ut = "lazy"
        skill_status: dict[str, str] = {}
        if isinstance(sk, dict):
            for k, v in sk.items():
                if not k:
                    continue
                vs = str(v).lower()
                if vs in ("in_progress", "completed"):
                    skill_status[str(k)[:64]] = vs
        return cls(
            topics=[str(t) for t in topics if t][:50],
            mistakes=[dict(m) for m in mistakes if isinstance(m, dict)][:40],
            progress={str(k): str(v) for k, v in progress.items() if k} if isinstance(progress, dict) else {},
            user_type=ut,
            skill_status=skill_status,
        )
