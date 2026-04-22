from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator


class BaseLLMProvider(ABC):
    @abstractmethod
    async def chat_completion(
        self,
        messages: list[dict[str, Any]],
        *,
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 300,
    ) -> str:
        pass

    @abstractmethod
    async def generate_stream(
        self,
        messages: list[dict[str, Any]],
        *,
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 300,
    ) -> AsyncGenerator[str, None]:
        """Yield text chunks for a streamed completion."""
        pass
