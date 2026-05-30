from __future__ import annotations

from app.wiki.cache import get_wiki_cache
from common.logger import get_logger

logger = get_logger(__name__)


class WikiSyncService:
    def __init__(self) -> None:
        self.cache = get_wiki_cache()

    async def sync_all(self, doc_tokens: list[str]) -> dict:
        result = {
            "total": len(doc_tokens),
            "cached": 0,
            "failed": 0,
        }
        for token in doc_tokens:
            try:
                from app.connectors.feishu.client import get_feishu_client

                client = get_feishu_client()
                content = await client.get_doc_content(token)
                await self.cache.set(token, content)
                result["cached"] += 1
            except Exception as exc:
                logger.error("wiki_sync_failed", token=token, error=str(exc))
                result["failed"] += 1

        return result

    async def invalidate(self, doc_token: str) -> None:
        await self.cache.delete(doc_token)
        logger.info("wiki_cache_invalidated", token=doc_token)
