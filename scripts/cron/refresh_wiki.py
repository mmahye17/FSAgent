#!/usr/bin/env python3
"""每小时增量刷新飞书文档缓存。"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.wiki.cache import get_wiki_cache
from common.logger import get_logger, setup_logging

logger = get_logger(__name__)

DOC_TOKENS = []


async def refresh_wiki() -> None:
    cache = get_wiki_cache()
    logger.info("refresh_wiki_start", doc_count=len(DOC_TOKENS))

    if DOC_TOKENS:
        count = await cache.warm_up(DOC_TOKENS)
        logger.info("refresh_wiki_done", cached=count)
    else:
        logger.info("refresh_wiki_skipped", reason="no_tokens_configured")


def main() -> None:
    setup_logging("INFO")
    asyncio.run(refresh_wiki())


if __name__ == "__main__":
    main()
