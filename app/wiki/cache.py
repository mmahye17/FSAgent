from __future__ import annotations

import json
from typing import Any

import redis.asyncio as aioredis

from app.config import get_settings
from common.logger import get_logger

logger = get_logger(__name__)


class WikiCache:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._redis: aioredis.Redis | None = None

    async def _get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            if self.settings.REDIS_CLUSTER_NODES:
                self._redis = aioredis.from_url(
                    f"redis://{self.settings.REDIS_CLUSTER_NODES.split(',')[0].strip()}",
                    password=self.settings.REDIS_CLUSTER_PASSWORD or None,
                    decode_responses=True,
                )
            else:
                self._redis = aioredis.from_url(
                    self.settings.REDIS_URL,
                    password=self.settings.REDIS_PASSWORD or None,
                    decode_responses=True,
                )
        return self._redis

    def _key(self, doc_id: str) -> str:
        return f"wiki:doc:{doc_id}"

    async def get(self, doc_id: str) -> dict[str, Any] | None:
        r = await self._get_redis()
        data = await r.get(self._key(doc_id))
        if data:
            return json.loads(data)
        return None

    async def set(self, doc_id: str, content: dict[str, Any], ttl: int | None = None) -> None:
        r = await self._get_redis()
        key = self._key(doc_id)
        await r.set(key, json.dumps(content, ensure_ascii=False))
        await r.expire(key, ttl or self.settings.WIKI_CACHE_TTL)

    async def delete(self, doc_id: str) -> None:
        r = await self._get_redis()
        await r.delete(self._key(doc_id))

    async def exists(self, doc_id: str) -> bool:
        r = await self._get_redis()
        return bool(await r.exists(self._key(doc_id)))

    async def get_batch(self, doc_ids: list[str]) -> dict[str, dict[str, Any]]:
        r = await self._get_redis()
        keys = [self._key(doc_id) for doc_id in doc_ids]
        values = await r.mget(keys)
        result = {}
        for doc_id, val in zip(doc_ids, values):
            if val:
                result[doc_id] = json.loads(val)
        return result

    async def warm_up(self, doc_ids: list[str]) -> int:
        from app.connectors.feishu.client import get_feishu_client

        client = get_feishu_client()
        count = 0

        for doc_id in doc_ids:
            try:
                content = await client.get_doc_content(doc_id)
                await self.set(doc_id, content)
                count += 1
            except Exception as exc:
                logger.error("wiki_cache_warm_failed", doc_id=doc_id, error=str(exc))

        logger.info("wiki_cache_warmed", count=count, total=len(doc_ids))
        return count


_wiki_cache: WikiCache | None = None


def get_wiki_cache() -> WikiCache:
    global _wiki_cache
    if _wiki_cache is None:
        _wiki_cache = WikiCache()
    return _wiki_cache
