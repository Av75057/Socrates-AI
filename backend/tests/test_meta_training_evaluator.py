from __future__ import annotations

import unittest
from pathlib import Path

from app.models.meta_training import MetaMessage, MetaTrainingPhase, MetaTrainingSessionState
from app.services.meta_training_evaluator import MetaTrainingEvaluator


class _FakeRouter:
    def __init__(self, response: dict) -> None:
        self.response = response

    def pedagogy_model(self) -> str:
        return "fake-model"

    async def call_model_json(self, messages, model, *, temperature=0.1, max_tokens=260):
        return self.response


class TestMetaTrainingEvaluator(unittest.IsolatedAsyncioTestCase):
    async def test_evaluator_parses_json_payload(self) -> None:
        evaluator = MetaTrainingEvaluator(prompt_path=Path("missing-does-not-matter.md"))
        state = MetaTrainingSessionState(
            session_id="meta-eval-1",
            thesis="Энтропия — это мера незнания.",
            topic_slug="entropy",
            phase=MetaTrainingPhase.REFLECTION,
            reflection_summary="Я не уверен, что тезис однозначен.",
        )
        state.transcript.extend(
            [
                MetaMessage(id="1", role="user", text="Что значит этот тезис?", phase=MetaTrainingPhase.ORIENTATION),
                MetaMessage(id="2", role="assistant", text="Уточни вопрос.", phase=MetaTrainingPhase.ORIENTATION),
                MetaMessage(id="3", role="user", text="Какую рамку выбрать?", phase=MetaTrainingPhase.EXPLORATION),
                MetaMessage(id="4", role="user", text="Я не уверен, что понимаю допущение.", phase=MetaTrainingPhase.SPARRING),
            ]
        )
        router = _FakeRouter(
            {
                "inquisitiveness": 7,
                "frame_agility": 5,
                "uncertainty_tolerance": 8,
                "assumption_detection": 6,
                "meta_reflection": 9,
                "comment": "Хорошо держит неопределенность.",
                "confidence": 0.92,
                "flags": ["high_performance"],
            }
        )
        result = await evaluator.evaluate(state, router)
        self.assertEqual(result.scores.meta_reflection, 9)
        self.assertEqual(result.evaluation.comment, "Хорошо держит неопределенность.")
        self.assertEqual(result.evaluation.confidence, 0.92)
        self.assertEqual(result.evaluation.flags, ["high_performance"])


if __name__ == "__main__":
    unittest.main()
