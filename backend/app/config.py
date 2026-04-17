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
    # OpenRouter: ключ и опции также можно задать только через env (см. model_router.py).


@lru_cache
def get_settings() -> Settings:
    return Settings()
