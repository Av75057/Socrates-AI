from __future__ import annotations

import unittest

from app.models.meta_training import MetaTrainingPhase, MetaTrainingSessionState
from app.services.meta_training_prompt_builder import MetaTrainingPromptBuilder


class TestMetaTrainingPromptBuilder(unittest.TestCase):
    def test_orientation_prompt_uses_orientation_block(self) -> None:
        builder = MetaTrainingPromptBuilder()
        state = MetaTrainingSessionState(
            session_id="meta-1",
            thesis="Энтропия — это мера незнания.",
            topic_slug="entropy",
            phase=MetaTrainingPhase.ORIENTATION,
        )
        bundle = builder.build(state)
        self.assertIn("Фаза 1: Ориентация", bundle.system_prompt)
        self.assertIn("Последние вопросы ученика", bundle.system_prompt)
        self.assertNotIn("Пример для Фазы 3", bundle.system_prompt)

    def test_sparring_prompt_includes_few_shot(self) -> None:
        builder = MetaTrainingPromptBuilder()
        state = MetaTrainingSessionState(
            session_id="meta-2",
            thesis="Наблюдатель влияет на реальность.",
            topic_slug="observer",
            phase=MetaTrainingPhase.SPARRING,
        )
        bundle = builder.build(state)
        self.assertIn("Сократический спарринг", bundle.system_prompt)
        self.assertIn("Пример для Фазы 3", bundle.system_prompt)


if __name__ == "__main__":
    unittest.main()
