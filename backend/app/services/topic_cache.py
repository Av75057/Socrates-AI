from __future__ import annotations

import json
import time
from hashlib import sha1
from typing import Any


_TOPICS_CACHE_VERSION_KEY = "socrates:topics:cache_version"


def _cache_key(namespace: str, version: str, payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    digest = sha1(encoded.encode("utf-8")).hexdigest()
    return f"socrates:topics:{namespace}:v{version}:{digest}"


async def get_topics_cache_version(client: Any) -> str:
    version = await client.get(_TOPICS_CACHE_VERSION_KEY)
    return str(version or "0")


async def invalidate_topics_cache(client: Any) -> None:
    await client.set(_TOPICS_CACHE_VERSION_KEY, str(int(time.time())))


async def read_topics_cache(client: Any, namespace: str, payload: dict[str, Any], ttl_seconds: int = 300) -> Any | None:
    version = await get_topics_cache_version(client)
    raw = await client.get(_cache_key(namespace, version, payload))
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except (TypeError, ValueError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    expires_at = int(data.get("expires_at") or 0)
    if expires_at and expires_at < int(time.time()):
        return None
    return data.get("payload")


async def write_topics_cache(client: Any, namespace: str, payload: dict[str, Any], value: Any, ttl_seconds: int = 300) -> None:
    version = await get_topics_cache_version(client)
    wrapped = {
        "expires_at": int(time.time()) + max(1, int(ttl_seconds)),
        "payload": value,
    }
    await client.set(
        _cache_key(namespace, version, payload),
        json.dumps(wrapped, ensure_ascii=False),
    )
