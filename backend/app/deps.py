"""Общие зависимости FastAPI."""

from __future__ import annotations

from fastapi import Depends

from app.config import Settings, get_settings
from app.services.redis_state import get_redis

_redis = None


async def redis_dep(settings: Settings = Depends(get_settings)):
    global _redis
    if _redis is None:
        _redis = await get_redis(settings.redis_url)
    return _redis
