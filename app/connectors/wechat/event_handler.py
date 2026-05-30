from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any

from app.connectors.base import IMUser, IMMessage
from app.harness.graph import AgentGraph
from common.logger import get_logger

logger = get_logger(__name__)


class WechatEventHandler:
    def __init__(self) -> None:
        self.agent = AgentGraph()

    async def handle(self, data: dict[str, Any]) -> None:
        msg_type = data.get("MsgType", "")

        handler_map = {
            "text": self._handle_text,
            "event": self._handle_event,
        }

        handler = handler_map.get(msg_type)
        if handler:
            await handler(data)
        else:
            logger.debug("wechat_unhandled_event", msg_type=msg_type)

    async def _handle_text(self, data: dict[str, Any]) -> None:
        content = data.get("Content", "")
        from_user = data.get("FromUserName", "")
        to_user = data.get("ToUserName", "")

        msg = IMMessage(
            message_id=data.get("MsgId", ""),
            content=content,
            sender=IMUser(user_id=from_user),
            group_id=to_user if "@@" in to_user else "",
            raw_data=data,
        )

        await self.agent.run(
            session_id=msg.group_id or msg.sender.user_id,
            user_id=msg.sender.user_id,
            message=msg.content,
            platform="wechat",
            group_id=msg.group_id,
        )

    async def _handle_event(self, data: dict[str, Any]) -> None:
        event = data.get("Event", "")
        logger.info("wechat_event", event=event)
