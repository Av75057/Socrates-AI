"""Провайдеры LLM (OpenRouter, Ollama) и глобальный вызов с fallback."""

from app.services.llm.global_call import (
    chat_completion_global_async,
    chat_completion_global_sync,
)
from app.services.llm.runtime import (
    get_effective_ollama_model,
    get_effective_provider,
    ping_ollama,
    set_runtime_llm,
    set_runtime_ollama_model,
    set_runtime_provider,
)

__all__ = [
    "chat_completion_global_async",
    "chat_completion_global_sync",
    "get_effective_ollama_model",
    "get_effective_provider",
    "ping_ollama",
    "set_runtime_llm",
    "set_runtime_ollama_model",
    "set_runtime_provider",
]
