from __future__ import annotations

from typing import Any

from app.skills.base import BaseSkill
from common.llm import get_llm_client
from common.logger import get_logger
from models.skill import SkillParameter

logger = get_logger(__name__)

MINUTES_SYSTEM_PROMPT = """你是一个会议纪要生成助手。根据提供的会议转写文本，生成结构化的会议纪要。

请按以下格式输出：
## 会议概要
(1-2句话概述)

## 讨论议题
1. 议题1 - 讨论要点
2. 议题2 - 讨论要点

## 决议
- 决议1
- 决议2

## 行动项
- [ ] 负责人: XXX - 任务描述 - 截止时间
- [ ] 负责人: XXX - 任务描述 - 截止时间"""


class MinutesFetchSkill(BaseSkill):
    name = "minutes.fetch"
    display_name = "获取会议记录"
    description = "获取飞书妙记转写文本"
    category = "minutes"
    parameters = [
        SkillParameter(name="source", type="string", description="数据源", required=False, default="feishu_minutes"),
        SkillParameter(name="meeting_id", type="string", description="会议ID", required=False),
    ]

    async def execute(self, **kwargs: Any) -> Any:
        meeting_id = kwargs.get("meeting_id", "")
        source = kwargs.get("source", "feishu_minutes")

        if source == "feishu_minutes" and meeting_id:
            from app.connectors.feishu.client import get_feishu_client
            client = get_feishu_client()
            data = await client.get_minutes_transcript(meeting_id)
            return {"text": str(data), "source": source}

        return {"text": "[模拟会议转写文本] 今天讨论产品评审流程优化方案...", "source": "mock"}


class MinutesGenerateSkill(BaseSkill):
    name = "minutes.generate"
    display_name = "生成会议纪要"
    description = "基于转写文本生成结构化纪要"
    category = "minutes"
    parameters = [
        SkillParameter(name="transcript", type="string", description="转写文本", required=False),
    ]

    async def execute(self, **kwargs: Any) -> Any:
        transcript = kwargs.get("transcript", "[会议转写文本]")
        llm = get_llm_client()

        summary = await llm.simple_prompt(
            system=MINUTES_SYSTEM_PROMPT,
            user=f"请为以下会议生成纪要：\n\n{transcript}",
        )
        return {"minutes": summary}


class MinutesExtractActionsSkill(BaseSkill):
    name = "minutes.extract_actions"
    display_name = "提炼行动项"
    description = "从纪要中提取行动项"
    category = "minutes"
    parameters = [
        SkillParameter(name="minutes_text", type="string", description="纪要文本", required=False),
    ]

    async def execute(self, **kwargs: Any) -> Any:
        minutes_text = kwargs.get("minutes_text", "")
        llm = get_llm_client()

        prompt = f"从以下会议纪要中提取所有行动项，每行一个，格式: 负责人 | 任务 | 截止时间\n\n{minutes_text}"
        actions = await llm.simple_prompt(
            system="你是一个任务提取助手。只提取行动项，不要其他内容。",
            user=prompt,
        )

        action_items = []
        for line in actions.strip().splitlines():
            parts = line.strip().split("|")
            if len(parts) >= 2:
                action_items.append({
                    "owner": parts[0].strip(),
                    "task": parts[1].strip(),
                    "deadline": parts[2].strip() if len(parts) > 2 else "未指定",
                })

        return {"actions": action_items, "count": len(action_items)}
