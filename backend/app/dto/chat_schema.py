from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = ""
    session_id: str = Field(..., min_length=1, max_length=128)
    action: Literal["none", "hint", "give_up"] = "none"
    conversation_id: int | None = Field(
        None,
        description="ID диалога в БД (только для авторизованных; session_id = session_key диалога)",
    )
    memory_user_id: str | None = Field(
        None,
        max_length=128,
        description="Стабильный id для долговременной памяти (иначе session_id)",
    )
    client_message_id: str | None = Field(
        None,
        max_length=64,
        description="Идентификатор клиентского сообщения для дедупликации повторных отправок",
    )
    assignment_id: int | None = Field(
        None,
        description="Назначение/домашнее задание, с которым связан диалог",
    )


class MemoryOut(BaseModel):
    topics: list[str] = Field(default_factory=list)
    mistakes: list[dict[str, Any]] = Field(default_factory=list)
    progress: dict[str, str] = Field(default_factory=dict)
    user_type: str = "lazy"
    skill_status: dict[str, str] = Field(default_factory=dict)
    thinking_profile: dict[str, Any] = Field(default_factory=dict)


class FallacyOut(BaseModel):
    has_fallacy: bool = False
    fallacy_type: str | None = None
    fallacy_description: str | None = None
    suggestion: str | None = None


class PedagogyOut(BaseModel):
    mode: str = "friendly"
    difficulty_level: int = 1
    last_response_depth: float = 0.0
    fallacy: FallacyOut = Field(default_factory=FallacyOut)


class ChatResponse(BaseModel):
    reply: str
    mode: str
    attempts: int
    frustration: int
    frustration_level: int
    user_type: str
    topic: str
    memory: MemoryOut
    skill_tree: dict[str, Any]
    pedagogy: PedagogyOut
    persisted_user_message_id: int | None = None
    persisted_assistant_message_id: int | None = None
    conversation_id: int | None = None
    session_key: str | None = None
