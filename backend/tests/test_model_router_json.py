from __future__ import annotations

import unittest

from app.services.model_router import ModelRouter


class _FakeJsonRouter(ModelRouter):
    def __init__(self, response: str) -> None:
        super().__init__(api_key="test", api_url="https://example.com/v1", custom_model_name="fake-model", use_openrouter_headers=False)
        self._response = response

    async def call_model(self, messages, model, *, temperature=0.1, max_tokens=300):
        return self._response


class TestModelRouterJson(unittest.IsolatedAsyncioTestCase):
    async def test_call_model_json_accepts_wrapped_object(self) -> None:
        router = _FakeJsonRouter('prefix {"ok": true, "score": 7} suffix')
        parsed = await router.call_model_json(
            [{"role": "system", "content": "Return JSON"}, {"role": "user", "content": "Now"}],
            "fake-model",
        )
        self.assertEqual(parsed["score"], 7)

    def test_parse_json_object_raises_for_missing_object(self) -> None:
        with self.assertRaises(ValueError):
            ModelRouter.parse_json_object("not a json payload")


if __name__ == "__main__":
    unittest.main()
