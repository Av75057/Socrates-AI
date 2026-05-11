from __future__ import annotations

import logging
import time
from dataclasses import replace
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import HTTPException

from app.dto.turn_result import TurnResult
from app.logging_context import log_context
from app.logging_setup import log_event
from app.services.answer_analyzer import AnswerAnalyzer
from app.services.adaptive_difficulty import (
    get_skill_id_for_topic_id,
    get_skill_mastery,
    get_target_difficulty,
    update_skill_mastery,
)
from app.services.dialogue_state import DialogueContext, DialogueStateProvider
from app.services.llm.runtime import get_effective_provider
from app.services.llm_logger import estimate_response_tokens, save_llm_log
from app.services.response_composer import TutorResponseComposer
from app.services.state_machine import DialoguePhase, validate_transition
from app.services.tutor_controller import TutorController
from app.db.session import SessionLocal

log = logging.getLogger(__name__)

LLMCall = Callable[[DialogueContext, Any], Awaitable[str]]


class InvalidDialogueTransitionError(RuntimeError):
    pass


async def default_llm_call(context: DialogueContext, plan: Any) -> str:
    if plan.immediate_reply is not None:
        return plan.immediate_reply
    return await context.router.generate(plan.prompt or "", plan.user_line, plan.mode)


class ChatOrchestrator:
    def __init__(
        self,
        *,
        state_provider: DialogueStateProvider | None = None,
        instruction_builder: Any | None = None,
        answer_analyzer: AnswerAnalyzer | None = None,
        response_composer: TutorResponseComposer | None = None,
        llm_call: LLMCall | None = None,
        controller_factory: Callable[[Any], TutorController] | None = None,
    ) -> None:
        from app.services.instruction_builder import InstructionBuilder

        self.state_provider = state_provider or DialogueStateProvider()
        self.instruction_builder = instruction_builder or InstructionBuilder()
        self.answer_analyzer = answer_analyzer or AnswerAnalyzer()
        self.response_composer = response_composer or TutorResponseComposer()
        self.llm_call = llm_call or default_llm_call
        self.controller_factory = controller_factory or (lambda router: TutorController(router))

    async def prepare_message(self, body: Any, redis_client: Any, db_user: Any, correlation_id: str) -> DialogueContext:
        context = await self.state_provider.load_or_create(
            body,
            redis_client,
            db_user,
            correlation_id,
            self.response_composer,
        )
        return context

    async def process_message(self, body: Any, redis_client: Any, db_user: Any, correlation_id: str) -> TurnResult:
        context = await self.prepare_message(body, redis_client, db_user, correlation_id)
        if context.duplicate_response is not None:
            return TurnResult(response=context.duplicate_response, mode=context.duplicate_response.mode)

        with log_context(
            correlation_id=correlation_id,
            user_id=context.prepared_turn.user_id,
            session_id=context.body.session_id,
            conversation_id=context.active_conversation_id,
            phase=context.current_phase.value,
        ):
            log_event(log, logging.INFO, "Turn started", action=context.body.action)
            controller = self.controller_factory(context.router)
            context.analysis = await self.answer_analyzer.analyze(context)
            self.apply_adaptive_difficulty(context)
            self.advance_state_for_turn(context)
            plan = self.instruction_builder.build_prompt(context, controller)
            started_at = time.perf_counter()
            raw_reply = await self.llm_call(context, plan)
            context.latency_ms = int((time.perf_counter() - started_at) * 1000)
            response = await self.response_composer.compose(context, controller, plan, raw_reply, source="chat")
            self.normalize_phase_for_persistence(context)
            await self._log_llm_if_needed(context, controller, raw_reply)
            await self.state_provider.save(context)
            log_event(log, logging.INFO, "Turn completed", action=context.body.action, latency_ms=context.latency_ms)
            return TurnResult(response=response, mode=plan.mode, raw_reply=context.original_reply, latency_ms=context.latency_ms)

    def apply_adaptive_difficulty(self, context: DialogueContext) -> None:
        db_user = getattr(context, "db_user", None)
        if db_user is None:
            return
        topic_id = getattr(context.state, "topic_id", None)
        if topic_id is None:
            return
        with SessionLocal() as db:
            skill_id = get_skill_id_for_topic_id(db, topic_id)
            if not skill_id:
                return
            if context.analysis is not None and context.msg_stripped and not context.cheat and not context.idle_turn:
                score = context.analysis.get("score")
                if score is not None:
                    mastery = update_skill_mastery(db, db_user.id, skill_id, float(score))
                    db.commit()
                else:
                    mastery = get_skill_mastery(db, db_user.id, skill_id)
            else:
                mastery = get_skill_mastery(db, db_user.id, skill_id)
        adaptive_difficulty = get_target_difficulty(mastery)
        context.configuration = replace(
            context.configuration,
            adaptive_difficulty=adaptive_difficulty,
        )

    async def finalize_stream_reply(self, context: DialogueContext, controller: TutorController, plan: Any, raw_reply: str) -> TurnResult:
        with log_context(
            correlation_id=context.correlation_id,
            user_id=context.prepared_turn.user_id,
            session_id=context.body.session_id,
            conversation_id=context.active_conversation_id,
            phase=context.current_phase.value,
        ):
            response = await self.response_composer.compose(context, controller, plan, raw_reply, source="chat_stream")
            self.normalize_phase_for_persistence(context)
            await self._log_llm_if_needed(context, controller, raw_reply)
            await self.state_provider.save(context)
            return TurnResult(response=response, mode=plan.mode, raw_reply=context.original_reply, latency_ms=context.latency_ms)

    def determine_runtime_phase(self, context: DialogueContext) -> DialoguePhase:
        if context.current_phase in {
            DialoguePhase.HINT_PROVIDED,
            DialoguePhase.INCORRECT_RETRY,
            DialoguePhase.GIVE_UP,
            DialoguePhase.CORRECT,
        } and not context.idle_turn and (context.msg_stripped or context.body.action in {"hint", "give_up"}):
            return DialoguePhase.AWAITING_ANSWER
        if context.current_phase == DialoguePhase.GREETING and not context.idle_turn:
            return DialoguePhase.AWAITING_ANSWER
        return context.current_phase

    def normalize_phase_for_persistence(self, context: DialogueContext) -> None:
        if context.current_phase in {
            DialoguePhase.CORRECT,
            DialoguePhase.INCORRECT_RETRY,
            DialoguePhase.GIVE_UP,
        }:
            self._transition(context, DialoguePhase.AWAITING_ANSWER)

    def advance_state_for_turn(self, context: DialogueContext) -> None:
        runtime_phase = self.determine_runtime_phase(context)
        if runtime_phase != context.current_phase:
            self._transition(context, runtime_phase)
        if context.body.action == "none" and context.msg_stripped and not context.cheat:
            self._transition(context, DialoguePhase.ANSWER_ANALYZED)
            self._transition(context, self.response_composer.determine_outcome_phase(context))
        elif context.body.action == "hint":
            self._transition(context, DialoguePhase.HINT_PROVIDED)
        elif context.body.action == "give_up":
            self._transition(context, DialoguePhase.GIVE_UP)

    def _transition(self, context: DialogueContext, new_phase: DialoguePhase) -> None:
        old_phase = context.current_phase
        if old_phase == new_phase:
            return
        if not validate_transition(old_phase, new_phase):
            log_event(
                log,
                logging.WARNING,
                "Invalid dialogue transition",
                phase=old_phase.value,
                phase_old=old_phase.value,
                phase_new=new_phase.value,
            )
            raise HTTPException(status_code=500, detail="Internal dialogue state error")
        context.current_phase = new_phase
        if not hasattr(context, "transition_history") or context.transition_history is None:
            context.transition_history = []
        context.transition_history.append(new_phase)
        log_event(
            log,
            logging.INFO,
            "Transition state",
            phase=new_phase.value,
            phase_old=old_phase.value,
            phase_new=new_phase.value,
        )

    async def _log_llm_if_needed(self, context: DialogueContext, controller: TutorController, raw_reply: str) -> None:
        if not controller.used_llm or not controller.last_prompt:
            return
        await save_llm_log(
            conversation_id=context.active_conversation_id,
            user_id=context.db_user.id if context.db_user else None,
            system_prompt=controller.last_prompt,
            user_messages=[{"role": "user", "content": controller.last_user_line or context.body.message}],
            model_params={
                "provider": get_effective_provider(),
                "model": context.router.select_model(controller.last_mode or context.state.mode),
            },
            raw_response=raw_reply,
            response_tokens=estimate_response_tokens(raw_reply),
            latency_ms=context.latency_ms,
        )
