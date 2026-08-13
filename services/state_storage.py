# ============================================================
#  services/state_storage.py
#  Vercel serverless uchun Redis (Vercel KV) yordamida
#  FSM holati va dialog ma'lumotlarini saqlash
# ============================================================

import json
import os
from typing import Any

# Redis mavjud bo'lsa ishlatamiz, bo'lmasa oddiy dict (lokal test uchun)
try:
    import aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from config import REDIS_URL

# ── Lokal fallback (Redis yo'q bo'lganda) ─────────────────────────────────────
_local_store: dict = {}


class StateStorage:
    """
    Har bir foydalanuvchi uchun dialog holatini saqlaydi.
    Key: user_id (int)
    Value: {"state": "...", "tpl_index": 0, "step": 0, "answers": {}}
    """

    def __init__(self):
        self._redis = None

    async def _get_redis(self):
        if not REDIS_AVAILABLE or not REDIS_URL:
            return None
        if self._redis is None:
            self._redis = await aioredis.from_url(
                REDIS_URL, encoding="utf-8", decode_responses=True
            )
        return self._redis

    async def get(self, user_id: int) -> dict | None:
        r = await self._get_redis()
        if r:
            raw = await r.get(f"user:{user_id}")
            return json.loads(raw) if raw else None
        return _local_store.get(user_id)

    async def set(self, user_id: int, data: dict, ttl: int = 3600) -> None:
        """TTL — sekund (standart 1 soat)"""
        r = await self._get_redis()
        if r:
            await r.setex(f"user:{user_id}", ttl, json.dumps(data, ensure_ascii=False))
        else:
            _local_store[user_id] = data

    async def delete(self, user_id: int) -> None:
        r = await self._get_redis()
        if r:
            await r.delete(f"user:{user_id}")
        else:
            _local_store.pop(user_id, None)

    async def exists(self, user_id: int) -> bool:
        r = await self._get_redis()
        if r:
            return bool(await r.exists(f"user:{user_id}"))
        return user_id in _local_store


# Global singleton
storage = StateStorage()
