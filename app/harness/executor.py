from __future__ import annotations

from app.harness.planner import PlanStep
from app.skills.registry import skill_registry
from common.logger import get_logger

logger = get_logger(__name__)


class PlanExecutor:
    async def execute_step(self, step: PlanStep) -> str:
        """执行单个步骤，返回观察结果"""
        # 没有 skill_name 的步骤是纯文本占位（比如最后的回复步骤）
        if not step.skill_name:
            step.status = "completed"
            return "完成"

        skill = skill_registry.get(step.skill_name)
        if not skill:
            step.status = "failed"
            msg = f"技能 '{step.skill_name}' 未注册"
            logger.warning("skill_not_found", skill_name=step.skill_name)
            return msg

        try:
            result = await skill.execute(**step.skill_params)
            step.status = "completed"
            return str(result)
        except Exception as exc:
            step.status = "failed"
            logger.error("step_execution_failed", step=step.step_id, error=str(exc))
            return f"执行失败: {exc}"
