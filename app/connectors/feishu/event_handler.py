from __future__ import annotations

import json
from typing import Any

from app.connectors.base import IMUser, IMMessage
from app.connectors.feishu.client import get_feishu_client
from app.harness.graph import AgentGraph
from common.logger import get_logger

logger = get_logger(__name__)


class FeishuEventHandler:
    def __init__(self) -> None:
        self.client = get_feishu_client()
        self.agent = AgentGraph()

    async def handle(self, data: dict[str, Any]) -> None:
        header = data.get("header", {})
        event_type = header.get("event_type", "")

        handler_map = {
            "im.message.receive_v1": self._handle_message,  #存的是函数，要是事件是im.message.receive_v1类型，就使用对应函数读取data
            "im.message.reaction.created_v1": self._handle_reaction,
        }

        handler = handler_map.get(event_type)
        if handler:
            await handler(data)
        else:
            logger.debug("飞书未抓取到事件类型", event_type=event_type)

    async def _handle_message(self, data: dict[str, Any]) -> None:

        event = data.get("event", {})
        message = event.get("message", {})
        sender = event.get("sender", {})

        if message.get("message_type") != "text":
            logger.debug("飞书消息不是文本消息", message=message)
            return

        content = json.loads(message.get("content", "{}"))
        text = content.get("text", "")

        mentions = message.get("mentions", [])
        bot_mentioned = any(
            # 判断是否被@
            m.get("name") in ("FSAgent", "fsagent") for m in mentions
        )

        im_msg = IMMessage(
            message_id=message.get("message_id", ""),
            content=text,
            sender=IMUser(
                user_id=sender.get("sender_id", {}).get("open_id", ""),
                display_name="",
            ),
            group_id=message.get("chat_id", ""),
            chat_type=message.get("chat_type", "group"),
            mentioned_bot=bot_mentioned,
            reply_to=message.get("root_id"),
            raw_data=data,
        )

        if bot_mentioned:
            await self.agent.run(
                session_id=im_msg.group_id or im_msg.sender.user_id,
                user_id=im_msg.sender.user_id,
                message=im_msg.content,
                platform="feishu",
                group_id=im_msg.group_id,
            )

    async def _handle_reaction(self, data: dict[str, Any]) -> None:
        event = data.get("event", {})
        logger.info("飞书的response", reaction=event.get("reaction_type"))
