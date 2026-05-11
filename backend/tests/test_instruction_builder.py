from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from app.services.instruction_builder import InstructionBuilder
from app.services.state_machine import DialoguePhase


def _build_context(*, analysis=None):
    return SimpleNamespace(
        analysis=analysis,
        configuration=SimpleNamespace(
            tutor_mode="friendly",
            difficulty_level=3,
            russian_only=True,
            persistent_profile="любит разбирать примеры",
            tutor_state={"step": 4, "topic": "fractions"},
        ),
        state=SimpleNamespace(topic="fractions", mode="question", phase=DialoguePhase.AWAITING_ANSWER),
        body=SimpleNamespace(message="Мой ответ", action="none"),
        memory=SimpleNamespace(user_type="lazy"),
    )


class TestInstructionBuilder(unittest.TestCase):
    def test_build_prompt_uses_empty_fallacy_instruction_without_analysis(self) -> None:
        context = _build_context(analysis=None)
        expected_plan = SimpleNamespace(prompt="prompt", user_line="user", mode="question", immediate_reply=None)
        controller = Mock()
        controller.plan_turn.return_value = expected_plan
        builder = InstructionBuilder()

        plan = builder.build_prompt(context, controller)

        self.assertIs(plan, expected_plan)
        controller.plan_turn.assert_called_once()
        args, kwargs = controller.plan_turn.call_args
        self.assertIs(args[0], context.state)
        self.assertEqual(args[1], "Мой ответ")
        self.assertEqual(args[2], "none")
        self.assertIs(args[3], context.memory)
        pedagogy = kwargs["pedagogy"]
        self.assertEqual(pedagogy.tutor_mode, "friendly")
        self.assertEqual(pedagogy.difficulty_level, 3)
        self.assertTrue(pedagogy.russian_only)
        self.assertEqual(pedagogy.fallacy_instruction, "")
        self.assertEqual(pedagogy.persistent_profile, "любит разбирать примеры")
        self.assertEqual(pedagogy.tutor_state, {"step": 4, "topic": "fractions"})

    def test_build_prompt_generates_and_passes_fallacy_instruction(self) -> None:
        analysis = {
            "has_fallacy": True,
            "fallacy_type": "straw_man",
            "fallacy_description": "Подмена тезиса",
            "suggestion": "Вернись к исходной формулировке",
        }
        context = _build_context(analysis=analysis)
        expected_plan = SimpleNamespace(prompt="prompt", user_line="user", mode="question", immediate_reply=None)
        controller = Mock()
        controller.plan_turn.return_value = expected_plan
        builder = InstructionBuilder()

        with patch(
            "app.services.instruction_builder.build_fallacy_instruction",
            return_value="fallacy-guidance",
        ) as build_fallacy:
            plan = builder.build_prompt(context, controller)

        self.assertIs(plan, expected_plan)
        build_fallacy.assert_called_once_with("friendly", analysis)
        pedagogy = controller.plan_turn.call_args.kwargs["pedagogy"]
        self.assertEqual(pedagogy.fallacy_instruction, "fallacy-guidance")
        self.assertEqual(pedagogy.tutor_mode, "friendly")
        self.assertEqual(pedagogy.difficulty_level, 3)


if __name__ == "__main__":
    unittest.main()
