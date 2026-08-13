# ============================================================
#  services/state_storage.py
#  Vercel serverless uchun Redis yordamida FSM holati saqlash
# ============================================================

import json
import os
from typing import Any

# Zamonaviy redis.asyncio ishlatamiz
try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except Exception:
    REDIS_AVAILABLE = False

from config import REDIS_URL

_local_store: dict = {}


class StateStorage:
    def __init__(self):
        self._redis = None

    async def _get_redis(self):
        if not REDIS_AVAILABLE or not REDIS_URL:
            return None
        if self._redis is None:
            try:
                self._redis = aioredis.from_url(
                    REDIS_URL, encoding="utf-8", decode_responses=True
                )
            except Exception:
                self._redis = None
        return self._redis

    async def get(self, user_id: int) -> dict | None:
        try:
            r = await self._get_redis()
            if r:
                raw = await r.get(f"user:{user_id}")
                return json.loads(raw) if raw else None
        except Exception:
            pass
        return _local_store.get(user_id)

    async def set(self, user_id: int, data: dict, ttl: int = 3600) -> None:
        try:
            r = await self._get_redis()
            if r:
                await r.setex(f"user:{user_id}", ttl, json.dumps(data, ensure_ascii=False))
                return
        except Exception:
            pass
        _local_store[user_id] = data

    async def delete(self, user_id: int) -> None:
        try:
            r = await self._get_redis()
            if r:
                await r.delete(f"user:{user_id}")
        except Exception:
            pass
        _local_store.pop(user_id, None)

    async def exists(self, user_id: int) -> bool:
        try:
            r = await self._get_redis()
            if r:
                return bool(await r.exists(f"user:{user_id}"))
        except Exception:
            pass
        return user_id in _local_store


storage = StateStorage()
