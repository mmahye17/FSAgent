#!/usr/bin/env python3
"""每天凌晨同步飞书通讯录到本地缓存。"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.connectors.feishu.client import get_feishu_client
from common.logger import get_logger, setup_logging

logger = get_logger(__name__)


async def sync_contacts() -> None:
    client = get_feishu_client()
    logger.info("sync_contacts_start")

    try:
        users = await client.get("/contact/v3/users", page_size=100)
        logger.info("sync_contacts_done", count=len(users.get("data", {}).get("items", [])))
    except Exception as exc:
        logger.error("sync_contacts_failed", error=str(exc))


def main() -> None:
    setup_logging("INFO")
    asyncio.run(sync_contacts())


if __name__ == "__main__":
    main()
