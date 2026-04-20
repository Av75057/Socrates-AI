from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Set to redis://localhost:6379/0 when using docker-compose Redis.
    redis_url: str = "memory"
    cors_origins: str = (
        "http://localhost:5173,http://127.0.0.1:5173,"
        "http://localhost:4173,http://127.0.0.1:4173"
    )
    # SQLAlchemy URL: sqlite:///./socrates.db или postgresql+psycopg://user:pass@localhost/socrates
    database_url: str = "sqlite:///./socrates.db"
    jwt_secret: str = "change-me-use-long-random-string"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24
    # Обновление навыков и педагогики в БД после ответов в чате
    skill_update_enabled: bool = True
    # Модель для редкой проверки logical_consistency (OpenRouter id)
    logical_consistency_model: str = "google/gemini-2.0-flash-lite"
    # Проверять логическую согласованность каждые N осмысленных ответов (0 = отключить LLM)
    logical_consistency_every_n: int = 5
    # Первый вопрос тьютора при POST /users/me/conversations (LLM)
    conversation_opening_enabled: bool = True
    # OpenRouter: ключ и опции также можно задать только через env (см. model_router.py).


@lru_cache
def get_settings() -> Settings:
    return Settings()
