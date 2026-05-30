#!/usr/bin/env python3
"""每天早上 8:00 生成今日待办摘要。"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from common.llm import get_llm_client
from common.logger import get_logger, setup_logging
from common.utils import utc_now
from app.memory.episodic import get_episodic_memory

logger = get_logger(__name__)


async def generate_daily_digest() -> None:
    logger.info("daily_digest_start")

    memory = get_episodic_memory()
    records = await memory.get_user_history(user_id="all", days=1, limit=100)

    context = "\n".join([r.content[:200] for r in records])

    if context:
        llm = get_llm_client()
        digest = await llm.simple_prompt(
            system="你是一个日常摘要助手。根据最近24小时的工作记录，生成简洁的每日摘要。",
            user=f"工作记录:\n{context}\n\n请生成今日摘要（200字以内）。",
        )
        logger.info("daily_digest_generated", length=len(digest))
    else:
        logger.info("daily_digest_skipped", reason="no_records")


def main() -> None:
    setup_logging("INFO")
    asyncio.run(generate_daily_digest())


if __name__ == "__main__":
    main()
