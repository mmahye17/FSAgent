from __future__ import annotations

import json

from dataclasses import dataclass, field
from typing import Any, Literal

from common.llm import get_llm_client
from common.logger import get_logger
from common.utils import generate_id

logger = get_logger(__name__)


@dataclass
class PlanStep:
    step_id: str = field(default_factory=generate_id)
    description: str = ""
    skill_name: str = ""
    skill_params: dict[str, Any] = field(default_factory=dict)
    depends_on: list[str] = field(default_factory=list)
    status: str = "pending"  # pending | running | completed | failed | skipped


@dataclass
class Plan:
    plan_id: str = field(default_factory=generate_id)
    intent: str = ""
    steps: list[PlanStep] = field(default_factory=list)
    current_step: int = 0
    observations: list[str] = field(default_factory=list)
    original_message: str = ""

    @property
    def finished(self) -> bool:
        return self.current_step >= len(self.steps)

    @property
    def current(self) -> PlanStep | None:
        if self.finished:
            return None
        return self.steps[self.current_step]

    def advance(self) -> PlanStep | None:
        if self.current_step < len(self.steps):
            self.steps[self.current_step].status = "completed"
        self.current_step += 1
        return self.current

    def pending_steps(self) -> list[PlanStep]:
        return [s for s in self.steps[self.current_step:] if s.status == "pending"]

#告诉llm有哪些技能
def _build_skills_prompt() -> str:
    from app.skills.registry import skill_registry

    lines = []
    for s in skill_registry.list_definitions():
        params_desc = ", ".join(
            f"{p.name}: {p.type}" + ("?" if not p.required else "")
            for p in s.parameters
        )
        lines.append(f"- {s.name}: {s.description} (参数: {params_desc})")
    return "\n".join(lines)


PLANNER_SYSTEM_PROMPT = """你是一个任务执行规划助手。根据用户意图和可用技能，生成执行计划。

可用技能:
{skills}

输出格式：严格的 JSON，不要输出其他内容。
{{
  "steps": [
    {{
      "description": "这一步要做什么（中文）",
      "skill_name": "要调用的技能名称",
      "skill_params": {{"参数名": "参数值"}},
      "depends_on": []
    }}
  ]
}}

规则：
1. 每个步骤必须使用可用技能列表中的技能名
2. depends_on 填依赖的步骤序号列表（从0开始），不依赖任何步骤就填 []
3. 一步一步来，每步只做一件事
4. 最后一步应该是回复用户（不依赖任何技能时，用 skill_name: "" 表示纯文本回复）
5. 步骤数量控制在 3-6 个"""

DECIDE_SYSTEM_PROMPT = """你是一个任务执行决策助手。根据执行进度，决定下一步动作。

当前计划:
{plan_summary}

已完成的步骤和结果:
{observations}

请决定下一步：
- "continue": 按计划继续执行下一步
- "replan": 当前计划有问题，需要重新规划剩余步骤（比如某步失败了需要换方案）
- "reply": 所有任务已完成，可以生成最终回复

只输出一个词：continue / replan / reply"""

REPLAN_SYSTEM_PROMPT = """你是一个任务执行规划助手。原计划执行中遇到了问题，需要重新规划剩余步骤。

可用技能:
{skills}

原始用户请求: {original_message}

已完成的步骤:
{completed_steps}

失败或需要调整的步骤:
{failed_steps}

请重新生成剩余步骤的 JSON：
{{
  "steps": [
    {{
      "description": "步骤描述",
      "skill_name": "技能名称",
      "skill_params": {{}},
      "depends_on": []
    }}
  ]
}}"""


class Planner:
    def __init__(self) -> None:
        self.llm = get_llm_client()
        self._skills_prompt = _build_skills_prompt()

    async def generate_plan(self, intent: str, user_message: str, context: str = "") -> Plan:
        """LLM 生成执行计划"""
        system = PLANNER_SYSTEM_PROMPT.format(skills=self._skills_prompt)
        user_prompt = f"意图: {intent}\n用户消息: {user_message}"
        if context:
            user_prompt += f"\n相关上下文: {context}"
        user_prompt += "\n\n请生成执行计划 JSON。"

        try:
            result = await self.llm.simple_prompt(system=system, user=user_prompt)
            plan_data = self._extract_json(result)
            steps = self._parse_steps(plan_data)
            logger.info("计划已生成", intent=intent, step_count=len(steps))
            return Plan(intent=intent, steps=steps, original_message=user_message)
        except Exception as exc:
            logger.error("计划生成失败", error=str(exc))
            return Plan(intent=intent, steps=[], original_message=user_message)

    async def decide_next(self, plan: Plan, last_observation: str) -> Literal["continue", "replan", "reply"]:
        """LLM 决策：继续 / 重规划 / 回复"""
        #列举已经完成的步骤
        completed = [
            f"[完成] {s.description} → {plan.observations[i] if i < len(plan.observations) else '无结果'}"
            for i, s in enumerate(plan.steps[:plan.current_step])
        ]
        #列举未完成的step
        pending = [f"[待执行] {s.description} ({s.skill_name})" for s in plan.pending_steps()]

        plan_summary = "\n".join(completed + pending) or "空计划"
        obs_text = last_observation or "无"

        try:
            result = await self.llm.simple_prompt(
                system=DECIDE_SYSTEM_PROMPT.format(
                    plan_summary=plan_summary,
                    observations=obs_text,
                ),
                user="请决定下一步动作。",
            )
            decision = result.strip().lower()
            if "replan" in decision:
                return "replan"
            elif "reply" in decision:
                return "reply"
            else:
                return "continue"
        except Exception:
            if plan.finished:
                return "reply"
            return "continue"

    async def replan(self, plan: Plan, last_error: str) -> Plan:
        """LLM 重新规划剩余步骤"""
        completed = "\n".join(
            f"{i}. {s.description} → 成功"
            for i, s in enumerate(plan.steps[:plan.current_step])
            if s.status == "completed"
        )
        failed = "\n".join(
            f"{i}. {s.description} → {last_error}"
            for i, s in enumerate(plan.steps[plan.current_step:plan.current_step+1])
        )

        system = REPLAN_SYSTEM_PROMPT.format(
            skills=self._skills_prompt,
            original_message=plan.original_message,
            completed_steps=completed or "无",
            failed_steps=failed or last_error,
        )

        try:
            result = await self.llm.simple_prompt(system=system, user="请生成新的剩余步骤。")
            data = self._extract_json(result)
            new_steps = self._parse_steps(data)

            # 保留已完成的步骤，替换剩余步骤
            plan.steps = plan.steps[:plan.current_step] + new_steps
            logger.info("计划重新生成成功", new_step_count=len(new_steps))
        except Exception as exc:
            logger.error("计划重新生成失败", error=str(exc))
            # replan 失败就标记剩余步骤跳过，直接结束
            for s in plan.steps[plan.current_step:]:
                s.status = "skipped"

        return plan

    def _extract_json(self, text: str) -> dict:
        """从 LLM 输出中提取 JSON"""
        text = text.strip()
        # 尝试找 ```json ... ``` 代码块
        if "```json" in text:
            start = text.index("```json") + 7
            end = text.index("```", start)
            text = text[start:end].strip()
        elif "```" in text:
            start = text.index("```") + 3
            end = text.index("```", start)
            text = text[start:end].strip()
        return json.loads(text)

    def _parse_steps(self, data: dict) -> list[PlanStep]:
        steps: list[PlanStep] = []
        raw = data.get("steps", data if isinstance(data, list) else [])
        if isinstance(raw, dict):
            raw = [raw]
        for i, s in enumerate(raw):
            steps.append(PlanStep(
                step_id=str(i),
                description=s.get("description", ""),
                skill_name=s.get("skill_name", ""),
                skill_params=s.get("skill_params", s.get("parameters", {})),
                depends_on=[str(d) for d in s.get("depends_on", [])],
            ))
        return steps
