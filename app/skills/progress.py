from __future__ import annotations

from typing import Any

from app.memory.manager import get_memory_manager
from app.skills.base import BaseSkill
from common.llm import get_llm_client
from common.logger import get_logger
from models.skill import SkillParameter

logger = get_logger(__name__)


class ProgressTrackSkill(BaseSkill):
    name = "progress.track"
    display_name = "追踪进度"
    description = "追踪历史任务/需求的进展状态"
    category = "progress"
    parameters = [
        SkillParameter(name="task_description", type="string", description="任务描述", required=True),
        SkillParameter(name="source_session_id", type="string", description="来源会话ID", required=False),
    ]

    async def execute(self, **kwargs: Any) -> Any:
        task_desc = kwargs.get("task_description", "")
        source_session_id = kwargs.get("source_session_id")

        memory = get_memory_manager()
        results = await memory.retrieve(task_desc, user_id="", top_k=10)

        context = "\n".join([r.content for r in results]) if results else "无相关历史记录"

        llm = get_llm_client()
        report = await llm.simple_prompt(
            system="你是一个项目进度追踪助手。根据历史记录分析任务进展。",
            user=f"任务: {task_desc}\n\n历史记录:\n{context}\n\n请汇报该任务的进展状态。",
        )

        return {
            "task": task_desc,
            "related_records": len(results),
            "report": report,
        }
