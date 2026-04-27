from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.models.meta_training import MetaTrainingAction, QuestionType


class MetaTrainingStartRequest(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=128)
    preferred_topic: str | None = Field(None, max_length=255)


class MetaTrainingMessageRequest(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=128)
    message: str = ""
    action: MetaTrainingAction = MetaTrainingAction.MESSAGE
    frame_name: str | None = Field(None, max_length=128)


class MetaTrainingEndRequest(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=128)
    summary: str | None = None
    confidence_label: str | None = Field(None, max_length=64)


class MetaTrainingResponse(BaseModel):
    session: dict[str, Any]
    reply: str | None = None
    messages: list[dict[str, Any]] = Field(default_factory=list)
    detected_question_type: QuestionType | None = None
