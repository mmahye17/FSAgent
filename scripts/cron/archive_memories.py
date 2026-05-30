#!/usr/bin/env python3
"""每天将工作记忆归档到情节记忆，清理过期数据。"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.memory.episodic import get_episodic_memory
from app.memory.manager import get_memory_manager
from common.logger import get_logger, setup_logging

logger = get_logger(__name__)


async def archive_memories() -> None:
    logger.info("archive_memories_start")

    episodic = get_episodic_memory()
    cleaned = await episodic.cleanup_expired()
    logger.info("archive_memories_done", cleaned_expired=cleaned)


def main() -> None:
    setup_logging("INFO")
    asyncio.run(archive_memories())


if __name__ == "__main__":
    main()
