"""Persistent tutor state (Redis-serializable)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.services.state_machine import DialoguePhase


@dataclass
class TutorState:
    attempts: int = 0
    frustration: int = 0
    mode: str = "question"  # question | hint | explain
    topic: str = ""
    topic_id: int | None = None
    user_type: str = "lazy"  # lazy | anxious | thinker
    phase: DialoguePhase = DialoguePhase.GREETING
    history: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "attempts": self.attempts,
            "frustration": self.frustration,
            "mode": self.mode,
            "topic": self.topic,
            "topic_id": self.topic_id,
            "user_type": self.user_type,
            "phase": self.phase.value,
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
        raw_phase = str(data.get("phase", DialoguePhase.GREETING.value) or DialoguePhase.GREETING.value)
        try:
            phase = DialoguePhase(raw_phase)
        except ValueError:
            phase = DialoguePhase.GREETING
        raw_topic_id = data.get("topic_id")
        try:
            topic_id = int(raw_topic_id) if raw_topic_id is not None else None
        except (TypeError, ValueError):
            topic_id = None
        return cls(
            attempts=int(data.get("attempts", 0)),
            frustration=int(data.get("frustration", 0)),
            mode=str(data.get("mode", "question")),
            topic=str(data.get("topic", "")),
            topic_id=topic_id,
            user_type=ut,
            phase=phase,
            history=hist,
        )
