from __future__ import annotations

import unittest
from pathlib import Path

from app.services.meta_training_question_classifier import MetaTrainingQuestionClassifier


class _FakeRouter:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def pedagogy_model(self) -> str:
        return "fake-model"

    async def call_model_json(self, messages, model, *, temperature=0.0, max_tokens=120):
        return self.payload


class TestMetaTrainingQuestionClassifier(unittest.IsolatedAsyncioTestCase):
    async def test_heuristic_classification_without_router(self) -> None:
        classifier = MetaTrainingQuestionClassifier(prompt_path=Path("missing.md"))
        qtype, assumption = await classifier.classify(
            "Что значит эта формулировка?",
            "Энтропия — это мера незнания.",
            None,
        )
        self.assertEqual(qtype.value, "conceptual")
        self.assertIsNotNone(assumption)

    async def test_router_can_override_question_type(self) -> None:
        classifier = MetaTrainingQuestionClassifier(prompt_path=Path("missing.md"))
        qtype, assumption = await classifier.classify(
            "Почему это вообще считается знанием?",
            "Тезис про знание.",
            _FakeRouter({"question_type": "meta", "assumption_hint": "Есть критерий знания."}),
        )
        self.assertEqual(qtype.value, "meta")
        self.assertEqual(assumption, "Есть критерий знания.")


if __name__ == "__main__":
    unittest.main()
