from __future__ import annotations

from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class MetaTrainingPhase(str, Enum):
    ORIENTATION = "orientation"
    EXPLORATION = "exploration"
    SPARRING = "sparring"
    REFLECTION = "reflection"
    COMPLETED = "completed"


class MetaTrainingAction(str, Enum):
    MESSAGE = "message"
    ADVANCE_PHASE = "advance_phase"
    SWITCH_FRAME = "switch_frame"


class QuestionType(str, Enum):
    FACTUAL = "factual"
    CONCEPTUAL = "conceptual"
    PROVOCATIVE = "provocative"
    META = "meta"


class MetaQuestion(BaseModel):
    id: str
    text: str
    question_type: QuestionType
    assumption: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class MetaFrameChoice(BaseModel):
    name: str
    reason: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class MetaMessage(BaseModel):
    id: str
    role: str
    text: str
    phase: MetaTrainingPhase
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class MetaScores(BaseModel):
    inquisitiveness: int = 0
    frame_agility: int = 0
    uncertainty_tolerance: int = 0
    assumption_detection: int = 0
    meta_reflection: int = 0

    def capped(self) -> MetaScores:
        return MetaScores(
            inquisitiveness=max(0, min(10, int(self.inquisitiveness))),
            frame_agility=max(0, min(10, int(self.frame_agility))),
            uncertainty_tolerance=max(0, min(10, int(self.uncertainty_tolerance))),
            assumption_detection=max(0, min(10, int(self.assumption_detection))),
            meta_reflection=max(0, min(10, int(self.meta_reflection))),
        )

    @property
    def total(self) -> int:
        s = self.capped()
        return (
            s.inquisitiveness
            + s.frame_agility
            + s.uncertainty_tolerance
            + s.assumption_detection
            + s.meta_reflection
        )


class MetaEvaluation(BaseModel):
    comment: str | None = None
    confidence: float | None = None
    flags: list[str] = Field(default_factory=list)


PHASE_DURATIONS_MINUTES: dict[MetaTrainingPhase, int] = {
    MetaTrainingPhase.ORIENTATION: 5,
    MetaTrainingPhase.EXPLORATION: 10,
    MetaTrainingPhase.SPARRING: 10,
    MetaTrainingPhase.REFLECTION: 5,
    MetaTrainingPhase.COMPLETED: 0,
}


class MetaTrainingSessionState(BaseModel):
    session_id: str
    user_id: str | None = None
    thesis: str
    topic_slug: str
    phase: MetaTrainingPhase = MetaTrainingPhase.ORIENTATION
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    phase_started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None
    questions: list[MetaQuestion] = Field(default_factory=list)
    frames: list[MetaFrameChoice] = Field(default_factory=list)
    transcript: list[MetaMessage] = Field(default_factory=list)
    scores: MetaScores = Field(default_factory=MetaScores)
    current_role_label: str = "Навигатор по вопросам"
    reflection_summary: str | None = None
    confidence_label: str | None = None
    evaluation: MetaEvaluation = Field(default_factory=MetaEvaluation)
    awarded_wisdom_points: int = 0
    reward_applied: bool = False

    def phase_deadline(self) -> datetime | None:
        minutes = PHASE_DURATIONS_MINUTES.get(self.phase, 0)
        if minutes <= 0:
            return None
        return self.phase_started_at + timedelta(minutes=minutes)

    def time_remaining_seconds(self, now: datetime | None = None) -> int:
        if self.phase == MetaTrainingPhase.COMPLETED:
            return 0
        current = now or datetime.now(timezone.utc)
        deadline = self.phase_deadline()
        if deadline is None:
            return 0
        return max(0, int((deadline - current).total_seconds()))

    def to_json(self) -> str:
        return self.model_dump_json()

    @classmethod
    def from_json(cls, raw: str) -> MetaTrainingSessionState | None:
        try:
            return cls.model_validate_json(raw)
        except (ValueError, TypeError):
            return None


def phase_role_label(phase: MetaTrainingPhase) -> str:
    if phase == MetaTrainingPhase.ORIENTATION:
        return "Навигатор по вопросам"
    if phase == MetaTrainingPhase.EXPLORATION:
        return "Навигатор по рамкам"
    if phase == MetaTrainingPhase.SPARRING:
        return "Защитник тезиса"
    if phase == MetaTrainingPhase.REFLECTION:
        return "Зеркало рефлексии"
    return "Итоговый разбор"


def session_public_payload(state: MetaTrainingSessionState) -> dict[str, Any]:
    scores = state.scores.capped()
    return {
        "session_id": state.session_id,
        "thesis": state.thesis,
        "topic_slug": state.topic_slug,
        "phase": state.phase.value,
        "phase_label": state.phase.value,
        "role_label": state.current_role_label,
        "time_remaining_seconds": state.time_remaining_seconds(),
        "questions": [q.model_dump(mode="json") for q in state.questions],
        "frames": [f.model_dump(mode="json") for f in state.frames],
        "scores": {
            **scores.model_dump(),
            "total": scores.total,
        },
        "reflection_summary": state.reflection_summary,
        "confidence_label": state.confidence_label,
        "evaluation": state.evaluation.model_dump(mode="json"),
        "awarded_wisdom_points": state.awarded_wisdom_points,
        "completed_at": state.completed_at.isoformat() if state.completed_at else None,
    }
