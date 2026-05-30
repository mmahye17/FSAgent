from __future__ import annotations

from typing import Any

from app.memory.manager import get_memory_manager
from app.skills.base import BaseSkill
from common.llm import get_llm_client
from common.logger import get_logger
from models.skill import SkillParameter

logger = get_logger(__name__)

WEEKLY_SYSTEM_PROMPT = """你是一个周报生成助手。根据提供的本周工作记录，生成结构化的周报。

请按以下格式输出：
## 本周工作摘要
(简要概括)

## 本周完成
- 完成项1
- 完成项2

## 进行中
- 进行项1
- 进行项2

## 下周计划
- 计划项1
- 计划项2

## 需关注的问题
- 问题1
- 问题2"""


class WeeklyReportSkill(BaseSkill):
    name = "weekly.report"
    display_name = "生成周报"
    description = "生成本周工作总结和下周计划"
    category = "report"
    parameters = [
        SkillParameter(name="period_start", type="string", description="周期开始日期", required=False),
        SkillParameter(name="period_end", type="string", description="周期结束日期", required=False),
        SkillParameter(name="user_id", type="string", description="用户ID", required=False),
    ]

    async def execute(self, **kwargs: Any) -> Any:
        period_start = kwargs.get("period_start", "")
        period_end = kwargs.get("period_end", "")
        user_id = kwargs.get("user_id", "")

        memory = get_memory_manager()
        query = f"本周工作 {period_start} {period_end}"
        results = await memory.retrieve_all_layers(query, user_id or "", top_k=20)

        context_parts = []
        for layer, items in results.items():
            for item in items:
                context_parts.append(f"[{layer}] {item.content}")

        context = "\n".join(context_parts) if context_parts else "暂无本周工作记录"

        llm = get_llm_client()
        report = await llm.simple_prompt(
            system=WEEKLY_SYSTEM_PROMPT,
            user=f"周期: {period_start} ~ {period_end}\n\n本周记录:\n{context}\n\n请生成周报。",
        )

        return {
            "period": {"start": period_start, "end": period_end},
            "report": report,
        }
