from __future__ import annotations

from typing import Any

from app.skills.base import BaseSkill
from common.logger import get_logger
from models.skill import SkillParameter

logger = get_logger(__name__)


class MeetingBookSkill(BaseSkill):
    name = "meeting.book"
    display_name = "预定会议"
    description = "预定会议并发送邀约"
    category = "meeting"
    requires_confirmation = True
    parameters = [
        SkillParameter(name="title", type="string", description="会议标题", required=True),
        SkillParameter(name="start_time", type="string", description="开始时间 (ISO格式)", required=True),
        SkillParameter(name="end_time", type="string", description="结束时间 (ISO格式)", required=True),
        SkillParameter(name="attendees", type="array", description="参会人列表", required=True),
        SkillParameter(name="description", type="string", description="会议描述", required=False),
    ]

    async def execute(self, **kwargs: Any) -> Any:
        title = kwargs.get("title", "未命名会议")
        attendees = kwargs.get("attendees", [])
        start_time = kwargs.get("start_time", "")
        end_time = kwargs.get("end_time", "")

        from app.connectors.feishu.client import get_feishu_client

        client = get_feishu_client()
        event = {
            "summary": title,
            "start_time": {"timestamp": start_time, "timezone": "Asia/Shanghai"},
            "end_time": {"timestamp": end_time, "timezone": "Asia/Shanghai"},
            "attendees": [{"type": "user", "user_id": uid} for uid in attendees],
        }
        result = await client.create_calendar_event("primary", event)
        return {
            "meeting_id": result.get("event_id", ""),
            "title": title,
            "start_time": start_time,
            "attendees": attendees,
            "status": "created",
        }


class MeetingNotifySkill(BaseSkill):
    name = "meeting.notify"
    display_name = "发送会议通知"
    description = "创建群聊并发送会议邀约"
    category = "meeting"
    parameters = [
        SkillParameter(name="title", type="string", description="会议标题", required=True),
        SkillParameter(name="attendees", type="array", description="参会人列表", required=True),
        SkillParameter(name="start_time", type="string", description="开始时间", required=True),
    ]

    async def execute(self, **kwargs: Any) -> Any:
        title = kwargs.get("title", "")
        attendees = kwargs.get("attendees", [])
        start_time = kwargs.get("start_time", "")

        from app.connectors.feishu.client import get_feishu_client

        client = get_feishu_client()
        group = await client.create_group(f"【会议】{title}", attendees)

        chat_id = group.get("data", {}).get("chat_id", "")
        if chat_id:
            content = f'{{"text":"【会议邀请】\\n主题: {title}\\n时间: {start_time}\\n参会人: {", ".join(attendees)}\\n\\n会议已创建，请准时参加。"}}'
            await client.send_message(chat_id, content)

        return {"group_id": chat_id, "status": "notified"}
