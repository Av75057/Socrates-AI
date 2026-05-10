from unittest.mock import AsyncMock, patch

import pytest

from app.services.llm.ollama_provider import OllamaProvider, strip_thinking_tags
from app.services.llm.runtime import list_ollama_models


@pytest.mark.asyncio
async def test_ollama_provider_chat_completion_parses_message():
    mock_resp = AsyncMock()
    mock_resp.raise_for_status = lambda: None
    mock_resp.json = lambda: {"message": {"role": "assistant", "content": "  hello  "}}

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client_cls.return_value = mock_client

        p = OllamaProvider("http://localhost:11434")
        out = await p.chat_completion(
            [{"role": "user", "content": "hi"}],
            model="qwen2.5:7b",
            temperature=0.7,
            max_tokens=100,
        )
        assert out == "hello"
        mock_client.post.assert_called_once()
        call_kw = mock_client.post.call_args
        assert call_kw[0][0] == "http://localhost:11434/api/chat"


def test_strip_thinking_tags_removes_hidden_reasoning():
    text = "<think>internal chain</think>\nКакой шаг будет первым?"
    assert strip_thinking_tags(text) == "Какой шаг будет первым?"


@pytest.mark.asyncio
async def test_ollama_provider_uses_default_model_and_strips_think_tags():
    mock_resp = AsyncMock()
    mock_resp.raise_for_status = lambda: None
    mock_resp.json = lambda: {
        "message": {"role": "assistant", "content": "<think>plan</think>\nС чего начнём?"}
    }

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client_cls.return_value = mock_client

        p = OllamaProvider("http://localhost:11434", default_model="socrates-tutor-rl")
        out = await p.chat_completion([{"role": "user", "content": "help"}])
        assert out == "С чего начнём?"
        payload = mock_client.post.call_args.kwargs["json"]
        assert payload["model"] == "socrates-tutor-rl"


def test_list_ollama_models_reads_tags_payload():
    class _Resp:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "models": [
                    {"name": "llama3.1:8b"},
                    {"model": "socrates-tutor-rl"},
                    {"name": "qwen2.5:7b-instruct"},
                ]
            }

    class _Client:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def get(self, _url):
            return _Resp()

    with patch("httpx.Client", _Client):
        assert list_ollama_models("http://localhost:11434") == [
            "llama3.1:8b",
            "qwen2.5:7b-instruct",
            "socrates-tutor-rl",
        ]


@pytest.mark.asyncio
async def test_ollama_provider_stream_preserves_spaces_between_chunks():
    class _StreamResponse:
        def raise_for_status(self):
            return None

        async def aiter_lines(self):
            lines = [
                '{"message":{"content":"Привет"},"done":false}',
                '{"message":{"content":" мир"},"done":false}',
                '{"message":{"content":"\\nКак дела?"},"done":false}',
                '{"done":true}',
            ]
            for line in lines:
                yield line

    class _StreamContext:
        async def __aenter__(self):
            return _StreamResponse()

        async def __aexit__(self, exc_type, exc, tb):
            return False

    class _Client:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        def stream(self, *args, **kwargs):
            return _StreamContext()

    with patch("httpx.AsyncClient", _Client):
        provider = OllamaProvider("http://localhost:11434", default_model="socrates-tutor-rl")
        chunks = []
        async for chunk in provider.generate_stream([{"role": "user", "content": "hi"}]):
            chunks.append(chunk)

    assert "".join(chunks) == "Привет мир\nКак дела?"
