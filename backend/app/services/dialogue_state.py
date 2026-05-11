from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from starlette.concurrency import run_in_threadpool

from app.db.models import Assignment, ClassStudent, User
from app.db.session import SessionLocal
from app.dto.chat_schema import ChatResponse
from app.logging_setup import log_event
from app.models.pedagogy import TutorMode
from app.models.tutor_configuration import TutorConfiguration
from app.services.cheat_detector import is_cheating
from app.services.conversation_db import (
    find_duplicate_turn,
    get_or_create_conversation_by_session_key,
    get_owned_conversation,
    hydrate_state_history_from_conversation_if_empty,
)
from app.services.conversation_db import get_owned_conversation as _get_owned_conversation
from app.services.learning_service import build_persistent_profile_for_prompt, hydrate_session_pedagogy_from_db
from app.services.memory_store import load_memory, save_memory
from app.services.model_router import ModelRouter
from app.services.pedagogy_store import load_pedagogy, save_pedagogy
from app.services.redis_state import load_state, save_state
from app.services.response_composer import initial_conversation_title, pedagogy_mode_str
from app.services.state_machine import DialoguePhase
from app.services.tutor_state_manager import DEFAULT_TUTOR_STATE, get_tutor_state
from app.services.user_settings_db import build_model_router_for_user, get_russian_only, get_tutor_mode

log = logging.getLogger(__name__)


@dataclass
class PreparedChatTurn:
    user_id: str
    conversation_id: str
    session_id: str
    message_text: str
    configuration: TutorConfiguration


@dataclass
class DialogueContext:
    body: Any
    redis_client: Any
    db_user: User | None
    prepared_turn: PreparedChatTurn
    state: Any
    memory: Any
    mid: str
    prev_skill: dict[str, str]
    pedagogy_state: Any
    router: ModelRouter
    analysis: dict[str, Any] | None = None
    active_conversation_id: int | None = None
    duplicate_response: ChatResponse | None = None
    correlation_id: str = ""
    msg_stripped: str = ""
    idle_turn: bool = False
    cheat: bool = False
    tutor_state: dict[str, Any] = field(default_factory=dict)
    transition_history: list[DialoguePhase] = field(default_factory=list)
    current_phase: DialoguePhase = DialoguePhase.GREETING
    configuration: TutorConfiguration | None = None
    original_reply: str = ""
    guarded_reply: str = ""
    reply_mode: str = ""
    latency_ms: int = 0


class DialogueStateProvider:
    async def load_or_create(self, body: Any, redis_client: Any, db_user: User | None, correlation_id: str, response_composer: Any) -> DialogueContext:
        msg_stripped = (body.message or "").strip()
        idle_turn = body.action == "none" and not msg_stripped
        active_conversation_id = body.conversation_id
        active_assignment_id = body.assignment_id

        if db_user and active_assignment_id is not None:
            active_assignment_id = await self._verify_assignment(db_user, active_assignment_id)

        if db_user and not idle_turn and active_conversation_id is None:
            active_conversation_id = await self._ensure_conversation(db_user, body.session_id, body, active_assignment_id)

        if active_conversation_id is not None:
            await self._verify_conversation_access(db_user, active_conversation_id, body.session_id)

        state = await load_state(redis_client, body.session_id)
        if db_user and active_conversation_id is not None:
            await self._hydrate_conversation_history(db_user.id, active_conversation_id, state)

        memory_user_id = str(db_user.id) if db_user else (body.memory_user_id or body.session_id).strip()
        memory = await load_memory(redis_client, memory_user_id)
        if memory.user_type in ("lazy", "anxious", "thinker"):
            state.user_type = memory.user_type
        pedagogy_state = await load_pedagogy(redis_client, body.session_id)

        persistent_profile = ""
        russian_only = True
        if db_user:
            tutor_mode, persistent_profile, russian_only = await self._hydrate_profile(db_user, pedagogy_state)
            try:
                pedagogy_state.mode = TutorMode(tutor_mode)
            except ValueError:
                pass

        cheat = bool(msg_stripped and is_cheating(msg_stripped))
        router = await self._build_router(db_user)
        tutor_state = dict(DEFAULT_TUTOR_STATE)
        if db_user and active_conversation_id is not None:
            tutor_state = await get_tutor_state(active_conversation_id)

        configuration = TutorConfiguration(
            topic=state.topic,
            difficulty_level=pedagogy_state.difficulty_level,
            adaptive_difficulty=None,
            tutor_mode=pedagogy_mode_str(pedagogy_state.mode),
            russian_only=russian_only,
            persistent_profile=persistent_profile,
            tutor_state=tutor_state,
        )
        prepared_turn = PreparedChatTurn(
            user_id=str(db_user.id) if db_user else memory_user_id,
            conversation_id=str(active_conversation_id or ""),
            session_id=body.session_id,
            message_text=body.message,
            configuration=configuration,
        )
        context = DialogueContext(
            body=body,
            redis_client=redis_client,
            db_user=db_user,
            prepared_turn=prepared_turn,
            state=state,
            memory=memory,
            mid=memory_user_id,
            prev_skill=dict(memory.skill_status),
            pedagogy_state=pedagogy_state,
            router=router,
            active_conversation_id=active_conversation_id,
            correlation_id=correlation_id,
            msg_stripped=msg_stripped,
            idle_turn=idle_turn,
            cheat=cheat,
            tutor_state=tutor_state,
            current_phase=state.phase,
            configuration=configuration,
        )
        duplicate_response = await self._load_duplicate_response(context, response_composer)
        context.duplicate_response = duplicate_response
        log_event(
            log,
            logging.INFO,
            "Dialogue state loaded",
            session_id=body.session_id,
            conversation_id=active_conversation_id,
            phase=state.phase.value,
            user_id=prepared_turn.user_id,
        )
        return context

    async def save(self, context: DialogueContext) -> None:
        context.state.phase = context.current_phase
        await save_state(context.redis_client, context.body.session_id, context.state)
        await save_memory(context.redis_client, context.mid, context.memory)
        await save_pedagogy(context.redis_client, context.body.session_id, context.pedagogy_state)
        log_event(
            log,
            logging.INFO,
            "Dialogue state saved",
            session_id=context.body.session_id,
            conversation_id=context.active_conversation_id,
            phase=context.current_phase.value,
            user_id=context.prepared_turn.user_id,
        )

    async def _verify_assignment(self, db_user: User, assignment_id: int) -> int:
        def _run() -> int | None:
            with SessionLocal() as db:
                assignment = db.get(Assignment, assignment_id)
                if assignment is None:
                    return None
                if db_user.role == "admin":
                    return assignment.id
                row = db.execute(
                    select(ClassStudent).where(
                        ClassStudent.class_id == assignment.class_id,
                        ClassStudent.student_id == db_user.id,
                    )
                ).scalar_one_or_none()
                return assignment.id if row is not None else None

        checked = await run_in_threadpool(_run)
        if checked is None:
            raise HTTPException(status_code=404, detail="Assignment not found")
        return checked

    async def _ensure_conversation(self, db_user: User, session_id: str, body: Any, assignment_id: int | None) -> int:
        def _run() -> int:
            with SessionLocal() as db:
                conversation = get_or_create_conversation_by_session_key(
                    db,
                    db_user.id,
                    session_id,
                    initial_conversation_title(body),
                    assignment_id=assignment_id,
                )
                return conversation.id

        return await run_in_threadpool(_run)

    async def _verify_conversation_access(self, db_user: User | None, conversation_id: int, session_id: str) -> None:
        if db_user is None:
            raise HTTPException(status_code=401, detail="Authentication required when conversation_id is set")

        def _run() -> str | None:
            with SessionLocal() as db:
                conversation = _get_owned_conversation(db, db_user.id, conversation_id)
                return conversation.session_key if conversation else None

        session_key = await run_in_threadpool(_run)
        if session_key is None:
            raise HTTPException(status_code=404, detail="Conversation not found")
        if session_id != session_key:
            raise HTTPException(
                status_code=400,
                detail="session_id must equal conversation.session_key for this conversation",
            )

    async def _hydrate_conversation_history(self, user_id: int, conversation_id: int, state: Any) -> None:
        def _run() -> None:
            with SessionLocal() as db:
                hydrate_state_history_from_conversation_if_empty(db, user_id, conversation_id, state)

        await run_in_threadpool(_run)

    async def _hydrate_profile(self, db_user: User, pedagogy_state: Any) -> tuple[str, str, bool]:
        def _run() -> tuple[str, str, bool]:
            with SessionLocal() as db:
                hydrate_session_pedagogy_from_db(db, db_user.id, pedagogy_state)
                tutor_mode = get_tutor_mode(db, db_user.id)
                profile = build_persistent_profile_for_prompt(db, db_user.id)
                russian_only = get_russian_only(db, db_user.id)
                return tutor_mode, profile, russian_only

        return await run_in_threadpool(_run)

    async def _build_router(self, db_user: User | None) -> ModelRouter:
        def _run() -> ModelRouter:
            if db_user is None:
                return ModelRouter()
            with SessionLocal() as db:
                return build_model_router_for_user(db, db_user.id)

        return await run_in_threadpool(_run)

    async def _load_duplicate_response(self, context: DialogueContext, response_composer: Any) -> ChatResponse | None:
        if not (context.db_user and context.active_conversation_id is not None and not context.idle_turn and context.body.client_message_id):
            return None

        def _run() -> tuple[int, int, str, dict[str, Any] | None] | None:
            with SessionLocal() as db:
                pair = find_duplicate_turn(
                    db,
                    context.db_user.id,
                    context.active_conversation_id,
                    context.body.client_message_id or "",
                )
                if pair is None:
                    return None
                user_msg, tutor_msg = pair
                return (
                    user_msg.id,
                    tutor_msg.id,
                    tutor_msg.content,
                    user_msg.fallacy_detected if isinstance(user_msg.fallacy_detected, dict) else None,
                )

        duplicate = await run_in_threadpool(_run)
        if duplicate is None:
            return None
        user_mid, tutor_mid, stored_reply, stored_fallacy = duplicate
        log_event(
            log,
            logging.INFO,
            "Duplicate turn reused",
            session_id=context.body.session_id,
            conversation_id=context.active_conversation_id,
            phase=context.state.phase.value,
            user_id=context.prepared_turn.user_id,
        )
        return response_composer.build_duplicate_response(context, stored_reply, stored_fallacy, user_mid, tutor_mid)
