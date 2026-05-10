from __future__ import annotations

import logging
from typing import Any

from app.logging_setup import log_event
from app.models.pedagogy import PedagogyTurnContext
from app.services.pedagogy_heuristics import build_fallacy_instruction
from app.services.tutor_controller import TutorController, TurnPlan

log = logging.getLogger(__name__)


class InstructionBuilder:
    def build_prompt(self, context: Any, controller: TutorController) -> TurnPlan:
        fallacy_instruction = ""
        if context.analysis is not None:
            fallacy_instruction = build_fallacy_instruction(
                context.configuration.tutor_mode,
                context.analysis,
            )
        pedagogy = PedagogyTurnContext(
            tutor_mode=context.configuration.tutor_mode,
            difficulty_level=context.configuration.difficulty_level,
            russian_only=context.configuration.russian_only,
            fallacy_instruction=fallacy_instruction,
            persistent_profile=context.configuration.persistent_profile,
            tutor_state=context.configuration.tutor_state,
        )
        plan = controller.plan_turn(
            context.state,
            context.body.message,
            context.body.action,
            context.memory,
            pedagogy=pedagogy,
        )
        log_event(log, logging.DEBUG, "Prompt built", phase=context.state.phase, action=context.body.action)
        return plan
