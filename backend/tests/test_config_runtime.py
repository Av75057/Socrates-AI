from __future__ import annotations

import unittest

from app.config import get_settings


class TestConfigRuntime(unittest.TestCase):
    def test_get_settings_returns_runtime_defaults_without_env(self) -> None:
        settings = get_settings()

        self.assertIsNotNone(settings)
        self.assertTrue(settings.database_url)
        self.assertTrue(settings.jwt_secret)
        self.assertIn(settings.llm_provider, {"openrouter", "openai", "ollama"})


if __name__ == "__main__":
    unittest.main()
