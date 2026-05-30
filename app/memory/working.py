from __future__ import annotations

import json
from typing import Any

import redis.asyncio as aioredis

from app.config import get_settings
from app.memory.base import MemoryStore
from common.logger import get_logger
from models.memory import MemoryEntry, MemorySearchRequest, MemorySearchResult

logger = get_logger(__name__)


class WorkingMemoryStore(MemoryStore):
    store_type = "working"

    def __init__(self) -> None:
        self.settings = get_settings()
        self._redis: aioredis.Redis | None = None

    async def _get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = aioredis.from_url(
                self.settings.REDIS_URL,
                password=self.settings.REDIS_PASSWORD or None,
                decode_responses=True,
            )
        return self._redis

    def _key(self, session_id: str) -> str:
        return f"working_memory:{session_id}"

    async def save(self, entry: MemoryEntry) -> None:
        r = await self._get_redis()
        key = self._key(entry.session_id or "global")
        ttl = entry.ttl_seconds or self.settings.SESSION_TTL_SECONDS

        await r.lpush(key, entry.model_dump_json())
        await r.ltrim(key, 0, self.settings.SESSION_MAX_MESSAGES - 1)
        await r.expire(key, ttl)

    async def get(self, memory_id: str) -> MemoryEntry | None:
        r = await self._get_redis()
        data = await r.get(f"memory:{memory_id}")
        if data:
            return MemoryEntry.model_validate_json(data)
        return None

    async def get_session_memories(self, session_id: str) -> list[MemoryEntry]:
        r = await self._get_redis()
        key = self._key(session_id)
        items = await r.lrange(key, 0, -1)
        return [MemoryEntry.model_validate_json(item) for item in items]

    async def search(self, request: MemorySearchRequest) -> list[MemorySearchResult]:
        results: list[MemorySearchResult] = []
        r = await self._get_redis()

        keys = await r.keys("working_memory:*")
        for key in keys:
            items = await r.lrange(key, 0, -1)
            for item_json in items:
                entry = MemoryEntry.model_validate_json(item_json)
                if request.query.lower() in entry.content.lower():
                    results.append(
                        MemorySearchResult(
                            memory_id=entry.memory_id,
                            content=entry.content,
                            score=0.5,
                            memory_type="working",
                            metadata=entry.metadata,
                            created_at=entry.created_at,
                        )
                    )

        results.sort(key=lambda x: x.score, reverse=True)
        return results[: request.top_k]

    async def delete(self, memory_id: str) -> None:
        r = await self._get_redis()
        await r.delete(f"memory:{memory_id}")

    async def clear_session(self, session_id: str) -> None:
        r = await self._get_redis()
        await r.delete(self._key(session_id))


_working_store: WorkingMemoryStore | None = None


def get_working_memory() -> WorkingMemoryStore:
    global _working_store
    if _working_store is None:
        _working_store = WorkingMemoryStore()
    return _working_store
