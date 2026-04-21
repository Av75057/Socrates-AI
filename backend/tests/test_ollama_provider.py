from unittest.mock import AsyncMock, patch

import pytest

from app.services.llm.ollama_provider import OllamaProvider


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
