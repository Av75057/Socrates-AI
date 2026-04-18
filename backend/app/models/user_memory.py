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
    thinking_profile: dict[str, Any] = field(default_factory=dict)
    thinking_history: list[dict[str, int]] = field(default_factory=list)  # последние оценки {d,l,c}
    thinking_meta: dict[str, Any] = field(default_factory=dict)  # steps_samples и др.

    def to_dict(self) -> dict[str, Any]:
        return {
            "topics": list(self.topics),
            "mistakes": list(self.mistakes),
            "progress": dict(self.progress),
            "user_type": self.user_type,
            "skill_status": dict(self.skill_status),
            "thinking_profile": dict(self.thinking_profile),
            "thinking_history": list(self.thinking_history),
            "thinking_meta": dict(self.thinking_meta),
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

        tp = data.get("thinking_profile") if isinstance(data.get("thinking_profile"), dict) else {}
        th = data.get("thinking_history") if isinstance(data.get("thinking_history"), list) else []
        tm = data.get("thinking_meta") if isinstance(data.get("thinking_meta"), dict) else {}

        thinking_history: list[dict[str, int]] = []
        for item in th[-8:]:
            if isinstance(item, dict) and all(k in item for k in ("d", "l", "c")):
                thinking_history.append(
                    {"d": int(item["d"]), "l": int(item["l"]), "c": int(item["c"])}
                )

        return cls(
            topics=[str(t) for t in topics if t][:50],
            mistakes=[dict(m) for m in mistakes if isinstance(m, dict)][:40],
            progress={str(k): str(v) for k, v in progress.items() if k} if isinstance(progress, dict) else {},
            user_type=ut,
            skill_status=skill_status,
            thinking_profile={str(k): v for k, v in tp.items()} if tp else {},
            thinking_history=thinking_history,
            thinking_meta={str(k): v for k, v in tm.items()} if tm else {},
        )
