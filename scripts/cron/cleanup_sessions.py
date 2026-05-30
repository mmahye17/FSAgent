#!/usr/bin/env python3
"""每小时清理过期会话。"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.harness.session import get_session_store
from common.logger import get_logger, setup_logging

logger = get_logger(__name__)


async def cleanup_sessions() -> None:
    store = get_session_store()
    logger.info("cleanup_sessions_start", active_before=store.active_count)

    # In-memory sessions are cleaned up by TTL in Redis
    # This provides in-memory cleanup for the session store
    to_remove = [
        sid for sid, s in store._sessions.items()
        if s.status in ("expired", "closed")
    ]
    for sid in to_remove:
        store.remove(sid)

    logger.info("cleanup_sessions_done", removed=len(to_remove), active_after=store.active_count)


def main() -> None:
    setup_logging("INFO")
    asyncio.run(cleanup_sessions())


if __name__ == "__main__":
    main()
