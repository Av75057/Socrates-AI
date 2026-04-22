"""Педагогическое состояние: режим тьютора, сложность, метрики ответов."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from pydantic import BaseModel, Field


class TutorMode(str, Enum):
    STRICT = "strict"
    FRIENDLY = "friendly"
    PROVOCATEUR = "provocateur"


@dataclass
class PedagogyTurnContext:
    """Контекст одного хода для промпта."""

    tutor_mode: str = "friendly"
    difficulty_level: int = 1
    russian_only: bool = True
    fallacy_instruction: str = ""
    persistent_profile: str = ""


class UserPedagogyState(BaseModel):
    session_id: str = ""
    mode: TutorMode = TutorMode.FRIENDLY
    difficulty_level: int = Field(1, ge=1, le=5)
    last_response_depth: float = 0.0
    common_fallacies: list[str] = Field(default_factory=list)
    consecutive_deep: int = 0
    consecutive_shallow: int = 0
    deep_turns_in_dialog: int = 0

    def to_json(self) -> str:
        return self.model_dump_json()

    @classmethod
    def from_json(cls, raw: str) -> UserPedagogyState | None:
        try:
            return cls.model_validate_json(raw)
        except (ValueError, TypeError):
            return None
