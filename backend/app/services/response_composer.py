from __future__ import annotations

import asyncio
import logging
from typing import Any

from fastapi import HTTPException
from starlette.concurrency import run_in_threadpool

from app.config import get_settings
from app.db.session import SessionLocal
from app.dto.chat_schema import ChatResponse, FallacyOut, MemoryOut, PedagogyOut
from app.logging_setup import log_event
from app.services.conversation_db import append_messages
from app.services.difficulty_adjuster import apply_after_user_turn, apply_hint_penalty
from app.services.learning_service import update_user_learning_progress_sync
from app.services.memory_manager import update_memory_after_turn
from app.services.skill_tree_manager import (
    align_tree_hint_with_session_topic,
    build_skill_tree_payload,
    canonical_subject_topic,
    resolve_track_hint,
)
from app.services.state_machine import DialoguePhase
from app.services.tutor_prompt import is_invalid_tutor_reply, is_tutor_answering_for_student
from app.services.tutor_state_manager import DEFAULT_TUTOR_STATE, update_tutor_state

log = logging.getLogger(__name__)


def line_for_memory_update(body: Any) -> str:
    message = (body.message or "").strip()
    if body.action == "give_up":
        return message or "(сдаюсь — нужно краткое объяснение и контрольный вопрос в конце)"
    if body.action == "hint":
        return message or "(запрошена подсказка)"
    return message


def pedagogy_mode_str(mode: Any) -> str:
    if mode is None:
        return "friendly"
    if hasattr(mode, "value"):
        return str(mode.value)
    normalized = str(mode).strip().lower()
    return normalized if normalized in ("strict", "friendly", "provocateur") else "friendly"


def initial_conversation_title(body: Any) -> str:
    seed = (body.message or "").strip()
    if not seed:
        seed = line_for_memory_update(body)
    seed = seed.strip()
    if not seed or seed.startswith("("):
        return "Новый диалог"
    return seed[:50]


def guard_tutor_reply(reply: str, *, session_id: str, conversation_id: int | None, source: str) -> str:
    text = str(reply or "").strip()
    if not is_tutor_answering_for_student(text) and not is_invalid_tutor_reply(text):
        return text
    log_event(
        log,
        logging.WARNING,
        "Tutor reply blocked by route guard",
        session_id=session_id,
        conversation_id=conversation_id,
    )
    return "Хорошо. С какой математической задачи начнём?"


def _fallacy_out(analysis: dict[str, Any] | None) -> FallacyOut:
    if not analysis:
        return FallacyOut()
    return FallacyOut(
        has_fallacy=bool(analysis.get("has_fallacy")),
        fallacy_type=analysis.get("fallacy_type") if analysis.get("has_fallacy") else None,
        fallacy_description=analysis.get("fallacy_description") if analysis.get("has_fallacy") else None,
        suggestion=analysis.get("suggestion") if analysis.get("has_fallacy") else None,
    )


def _memory_out(memory: Any) -> MemoryOut:
    data = memory.to_dict()
    return MemoryOut(
        topics=data["topics"],
        mistakes=data["mistakes"],
        progress=data["progress"],
        user_type=data["user_type"],
        skill_status=data.get("skill_status") or {},
        thinking_profile=data.get("thinking_profile") or {},
    )


def _next_tutor_state(context: Any) -> dict[str, Any]:
    current = dict(context.tutor_state or DEFAULT_TUTOR_STATE)
    attempted = list(current.get("attempted_concepts") or [])
    line = line_for_memory_update(context.body).strip()
    if line:
        attempted.append(line[:120])
    return {
        "level": int(context.pedagogy_state.difficulty_level),
        "mode": pedagogy_mode_str(context.pedagogy_state.mode),
        "step": int(current.get("step") or 0) + 1,
        "stuck": bool(context.state.frustration >= 2 or context.body.action in ("hint", "give_up")),
        "last_fallacy": (
            context.analysis.get("fallacy_type")
            if context.analysis and context.analysis.get("has_fallacy")
            else current.get("last_fallacy")
        ),
        "topic": context.state.topic or current.get("topic") or "general",
        "attempted_concepts": attempted[-8:],
    }


class TutorResponseComposer:
    def determine_outcome_phase(self, context: Any) -> DialoguePhase:
        if context.body.action == "hint":
            return DialoguePhase.HINT_PROVIDED
        if context.body.action == "give_up":
            return DialoguePhase.GIVE_UP
        if context.idle_turn or context.cheat or not context.msg_stripped:
            return context.current_phase
        if context.analysis is None:
            return DialoguePhase.AWAITING_ANSWER
        depth = float(context.analysis.get("depth_combined") or 0.0)
        if depth >= 0.7:
            return DialoguePhase.CORRECT
        if context.state.attempts >= 4:
            return DialoguePhase.GIVE_UP
        return DialoguePhase.INCORRECT_RETRY

    async def compose(self, context: Any, controller: Any, plan: Any, raw_reply: str, *, source: str) -> ChatResponse:
        try:
            original_reply = await controller.finalize_planned_reply(context.state, plan, raw_reply, allow_retry=True)
        except Exception as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        guarded_reply = guard_tutor_reply(
            original_reply,
            session_id=context.body.session_id,
            conversation_id=context.active_conversation_id,
            source=source,
        )
        controller.commit_turn(context.state, plan, guarded_reply)
        context.original_reply = original_reply
        context.guarded_reply = guarded_reply
        context.reply_mode = plan.mode
        context.state.mode = plan.mode

        if not context.cheat and not context.idle_turn:
            context.memory = update_memory_after_turn(context.memory, context.state, line_for_memory_update(context.body), plan.mode)

        if context.body.action == "hint":
            apply_hint_penalty(context.pedagogy_state)
        elif context.body.action == "none" and context.msg_stripped and not context.cheat and context.analysis is not None:
            apply_after_user_turn(context.pedagogy_state, float(context.analysis.get("depth_combined") or 0.0))

        if context.db_user and get_settings().skill_update_enabled:
            if not context.cheat and not context.idle_turn and context.body.action == "none" and context.msg_stripped and context.analysis:
                user_id = context.db_user.id
                user_text = context.msg_stripped
                analysis = dict(context.analysis)
                difficulty_level = int(context.pedagogy_state.difficulty_level)
                topic_id = context.state.topic_id

                async def _learning_bg() -> None:
                    try:
                        await run_in_threadpool(
                            update_user_learning_progress_sync,
                            user_id,
                            user_text,
                            analysis,
                            difficulty_level,
                            topic_id,
                        )
                    except Exception:
                        log.exception("learning progress background task failed")

                asyncio.create_task(_learning_bg())

        skill_tree = self._build_skill_tree(context)
        pedagogy = PedagogyOut(
            mode=pedagogy_mode_str(context.pedagogy_state.mode),
            difficulty_level=context.pedagogy_state.difficulty_level,
            last_response_depth=round(context.pedagogy_state.last_response_depth, 3),
            fallacy=_fallacy_out(context.analysis),
        )
        persisted_pair = await self._persist_conversation_turn(context, guarded_reply)
        if context.active_conversation_id is not None:
            asyncio.create_task(update_tutor_state(context.active_conversation_id, _next_tutor_state(context)))
        response = ChatResponse(
            reply=guarded_reply,
            mode=plan.mode,
            attempts=context.state.attempts,
            frustration=context.state.frustration,
            frustration_level=min(3, context.state.frustration),
            user_type=context.state.user_type if context.state.user_type in ("lazy", "anxious", "thinker") else "lazy",
            topic=context.state.topic,
            memory=_memory_out(context.memory),
            skill_tree=skill_tree,
            pedagogy=pedagogy,
            persisted_user_message_id=persisted_pair[0] if persisted_pair else None,
            persisted_assistant_message_id=persisted_pair[1] if persisted_pair else None,
            conversation_id=context.active_conversation_id,
            session_key=context.body.session_id,
        )
        log_event(log, logging.INFO, "Turn composed", phase=context.state.phase, latency_ms=context.latency_ms)
        return response

    def build_duplicate_response(self, context: Any, stored_reply: str, stored_fallacy: dict[str, Any] | None, user_message_id: int, assistant_message_id: int) -> ChatResponse:
        skill_tree = self._build_skill_tree(context)
        pedagogy = PedagogyOut(
            mode=pedagogy_mode_str(context.pedagogy_state.mode),
            difficulty_level=context.pedagogy_state.difficulty_level,
            last_response_depth=round(context.pedagogy_state.last_response_depth, 3),
            fallacy=_fallacy_out(stored_fallacy),
        )
        return ChatResponse(
            reply=stored_reply,
            mode=context.state.mode,
            attempts=context.state.attempts,
            frustration=context.state.frustration,
            frustration_level=min(3, context.state.frustration),
            user_type=context.state.user_type if context.state.user_type in ("lazy", "anxious", "thinker") else "lazy",
            topic=context.state.topic,
            memory=_memory_out(context.memory),
            skill_tree=skill_tree,
            pedagogy=pedagogy,
            persisted_user_message_id=user_message_id,
            persisted_assistant_message_id=assistant_message_id,
            conversation_id=context.active_conversation_id,
            session_key=context.body.session_id,
        )

    def _build_skill_tree(self, context: Any) -> dict[str, Any]:
        tree_hint = resolve_track_hint(context.state.topic, context.memory, context.body.message)
        subject = canonical_subject_topic(context.msg_stripped)
        if subject:
            tree_hint = f"{subject} {tree_hint}".strip()
        tree_hint = align_tree_hint_with_session_topic(tree_hint, context.state.topic)
        return build_skill_tree_payload(
            context.prev_skill,
            dict(context.memory.skill_status),
            track_hint=tree_hint,
            topic=context.state.topic,
        )

    async def _persist_conversation_turn(self, context: Any, reply: str) -> tuple[int, int] | None:
        if not (context.db_user and context.active_conversation_id and not context.idle_turn):
            return None
        user_line = context.msg_stripped if context.body.action == "none" and context.msg_stripped else line_for_memory_update(context.body)
        fallacy_payload: dict[str, Any] | None = None
        if context.analysis:
            fallacy_payload = {
                "has_fallacy": bool(context.analysis.get("has_fallacy")),
                "fallacy_type": context.analysis.get("fallacy_type"),
                "fallacy_description": context.analysis.get("fallacy_description"),
                "suggestion": context.analysis.get("suggestion"),
                "depth_combined": context.analysis.get("depth_combined"),
            }
        conversation_id = context.active_conversation_id
        user_id = context.db_user.id

        def _persist_turn() -> tuple[int, int] | None:
            with SessionLocal() as db:
                return append_messages(
                    db,
                    conversation_id,
                    user_id,
                    user_line,
                    reply,
                    fallacy_payload,
                    client_message_id=context.body.client_message_id,
                )

        return await run_in_threadpool(_persist_turn)
