from __future__ import annotations

from typing import Any

from app.connectors.feishu.client import get_feishu_client
from app.mcp.tools.base import MCPTool
from common.logger import get_logger

logger = get_logger(__name__)


class FeishuSendMessageTool(MCPTool):
    name = "feishu.im.message.send"
    description = "发送飞书消息到指定会话"
    parameters = {
        "receive_id": {"type": "string", "description": "接收者ID（chat_id 或 open_id）"},
        "content": {"type": "string", "description": "消息内容（JSON字符串）"},
        "msg_type": {"type": "string", "description": "消息类型，默认 text"},
    }

    async def execute(self, **kwargs: Any) -> Any:
        client = get_feishu_client()
        return await client.send_message(
            receive_id=kwargs["receive_id"],
            content=kwargs["content"],
            msg_type=kwargs.get("msg_type", "text"),
        )


class FeishuCalendarQueryTool(MCPTool):
    name = "feishu.calendar.freebusy"
    description = "查询飞书用户忙闲状态"
    parameters = {
        "user_ids": {"type": "array", "items": {"type": "string"}, "description": "用户ID列表"},
        "start_time": {"type": "string", "description": "开始时间 ISO格式"},
        "end_time": {"type": "string", "description": "结束时间 ISO格式"},
    }

    async def execute(self, **kwargs: Any) -> Any:
        client = get_feishu_client()
        return await client.get_freebusy(
            user_ids=kwargs["user_ids"],
            start_time=kwargs["start_time"],
            end_time=kwargs["end_time"],
        )


class FeishuCalendarCreateTool(MCPTool):
    name = "feishu.calendar.create"
    description = "创建飞书日历事件"
    parameters = {
        "calendar_id": {"type": "string", "description": "日历ID"},
        "event": {"type": "object", "description": "事件数据"},
    }

    async def execute(self, **kwargs: Any) -> Any:
        client = get_feishu_client()
        return await client.create_calendar_event(
            calendar_id=kwargs["calendar_id"],
            event=kwargs["event"],
        )


class FeishuGroupCreateTool(MCPTool):
    name = "feishu.im.group.create"
    description = "创建飞书群聊"
    parameters = {
        "name": {"type": "string", "description": "群名称"},
        "user_ids": {"type": "array", "items": {"type": "string"}, "description": "初始成员ID列表"},
    }

    async def execute(self, **kwargs: Any) -> Any:
        client = get_feishu_client()
        return await client.create_group(
            name=kwargs["name"],
            user_ids=kwargs["user_ids"],
        )


class FeishuUserQueryTool(MCPTool):
    name = "feishu.contact.user"
    description = "查询飞书用户信息"
    parameters = {
        "user_id": {"type": "string", "description": "用户ID"},
    }

    async def execute(self, **kwargs: Any) -> Any:
        client = get_feishu_client()
        return await client.get_user(user_id=kwargs["user_id"])


class FeishuDocContentTool(MCPTool):
    name = "feishu.doc.content"
    description = "获取飞书文档内容"
    parameters = {
        "doc_token": {"type": "string", "description": "文档Token"},
    }

    async def execute(self, **kwargs: Any) -> Any:
        client = get_feishu_client()
        return await client.get_doc_content(doc_token=kwargs["doc_token"])


class FeishuMinutesTranscriptTool(MCPTool):
    name = "feishu.minutes.transcript"
    description = "获取飞书妙记转写文本"
    parameters = {
        "minutes_token": {"type": "string", "description": "妙记Token"},
    }

    async def execute(self, **kwargs: Any) -> Any:
        client = get_feishu_client()
        return await client.get_minutes_transcript(minutes_token=kwargs["minutes_token"])
