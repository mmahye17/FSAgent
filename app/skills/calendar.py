from __future__ import annotations

from typing import Any

from app.skills.base import BaseSkill
from common.logger import get_logger
from models.skill import SkillParameter

logger = get_logger(__name__)


class CalendarQuerySkill(BaseSkill):
    name = "calendar.query"
    display_name = "查询日程"
    description = "查询用户忙闲状态"
    category = "calendar"
    parameters = [
        SkillParameter(name="user_ids", type="array", description="用户ID列表", required=True),
        SkillParameter(name="start_time", type="string", description="开始时间", required=True),
        SkillParameter(name="end_time", type="string", description="结束时间", required=True),
    ]

    async def execute(self, **kwargs: Any) -> Any:
        user_ids = kwargs.get("user_ids", [])
        start_time = kwargs.get("start_time", "")
        end_time = kwargs.get("end_time", "")

        from app.connectors.feishu.client import get_feishu_client

        client = get_feishu_client()
        result = await client.get_freebusy(user_ids, start_time, end_time)

        return {
            "user_ids": user_ids,
            "time_range": {"start": start_time, "end": end_time},
            "freebusy": result,
        }
