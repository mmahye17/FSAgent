from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.harness.executor import PlanExecutor
from app.harness.intent import IntentRecognizer, IntentType
from app.harness.planner import Plan, Planner
from app.harness.session import Session, get_session_store
from app.memory.manager import get_memory_manager
from common.llm import get_llm_client
from common.logger import get_logger
from common.utils import generate_id

logger = get_logger(__name__)

REPLY_SYSTEM_PROMPT = """你是一个智能办公助手 FSAgent。根据执行结果，用友好自然的语气回复用户。
回复要简洁、信息完整，包含所有关键信息（时间、地点、链接、人员等）。
使用中文回复。"""

MAX_LOOP = 10  # 最多循环10轮，防止死循环


@dataclass
class AgentResult:
    reply: str = ""
    tool_calls_made: list[str] = field(default_factory=list)
    session_id: str = ""
    plan: Plan | None = None


class AgentGraph:
    def __init__(self) -> None:
        self.intent = IntentRecognizer()
        self.planner = Planner()
        self.executor = PlanExecutor()
        self.llm = get_llm_client()
        self.memory = get_memory_manager()
        self.sessions = get_session_store()

    async def run(
        self,
        session_id: str,
        user_id: str,
        message: str,
        platform: str = "api",
        group_id: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> AgentResult:
        session = self.sessions.get_or_create(
            session_id=session_id,
            user_id=user_id,
            platform=platform,
            group_id=group_id,
        )
        session.add_message("user", message)

        try:
            # Step 1: 意图识别
            intent_type = self.intent.quick_match(message)
            if intent_type == IntentType.GENERAL_CHAT:
                intent_type = await self.intent.recognize(message)

            logger.info("意图识别", session_id=session_id, intent=intent_type.value)

            # Step 2: 检索记忆上下文
            memory_results = await self.memory.retrieve(query=message, user_id=user_id)
            context = "\n".join([r.content for r in memory_results]) if memory_results else ""

            # Step 3: LLM 动态生成计划
            plan = await self.planner.generate_plan(intent_type.value, message, context)

            if not plan.steps:
                reply = await self._simple_reply(session, message, context)
                session.add_message("assistant", reply)
                return AgentResult(reply=reply, session_id=session_id)

            # Step 4: Plan → Execute → Observe → Decide 循环
            loop = 0
            while loop < MAX_LOOP:
                loop += 1
                current = plan.current
                if current is None:
                    break  # 计划执行完毕

                # 检查依赖
                if not self._dependencies_met(current, plan):
                    current.status = "skipped"
                    plan.observations.append(f"跳过 {current.description}: 依赖未完成")
                    plan.advance()
                    continue

                # 执行当前步骤
                logger.info("执行步骤", step=current.step_id, skill=current.skill_name)
                observation = await self.executor.execute_step(current)
                plan.observations.append(observation)

                # 如果失败，让 LLM 决定是否重规划
                if current.status == "failed":
                    decision = await self.planner.decide_next(plan, observation)
                    if decision == "replan":
                        plan = await self.planner.replan(plan, observation)
                        continue  # 重新执行（可能换了新步骤）
                    elif decision == "reply":
                        break

                plan.advance()

                # 每步执行后让 LLM 决策
                if not plan.finished:
                    decision = await self.planner.decide_next(plan, observation)
                    if decision == "replan":
                        plan = await self.planner.replan(plan, observation)
                    elif decision == "reply":
                        break
                    # continue → 继续循环

            # Step 5: 合成回复
            tool_calls = [s.skill_name for s in plan.steps if s.skill_name]
            reply = await self._synthesize_reply(message, plan)

            session.add_message("assistant", reply)

            # Step 6: 保存记忆
            await self.memory.save_working(
                __import__("models.memory", fromlist=["MemoryEntry"]).MemoryEntry(
                    memory_id=generate_id(),
                    session_id=session_id,
                    user_id=user_id,
                    content=f"用户: {message}\n助手: {reply}",
                    memory_type="working",
                    metadata={
                        "intent": intent_type.value,
                        "tool_calls": ",".join(tool_calls),
                    },
                )
            )

            return AgentResult(
                reply=reply,
                tool_calls_made=tool_calls,
                session_id=session_id,
                plan=plan,
            )

        except Exception as exc:
            logger.error("Agent运行出错", error=str(exc))
            reply = f"抱歉，处理你的请求时出现了问题：{exc}"
            session.add_message("assistant", reply)
            return AgentResult(reply=reply, session_id=session_id)

    def _dependencies_met(self, step: Any, plan: Plan) -> bool:
        for dep_id in step.depends_on:
            if dep_id.isdigit():
                dep_step = plan.steps[int(dep_id)] if int(dep_id) < len(plan.steps) else None
                if dep_step and dep_step.status != "completed":
                    return False
        return True

    async def _synthesize_reply(self, message: str, plan: Plan) -> str:
        obs_text = "\n".join(
            f"步骤{i+1} ({s.description}): {plan.observations[i] if i < len(plan.observations) else '无结果'}"
            for i, s in enumerate(plan.steps)
        )

        try:
            return await self.llm.simple_prompt(
                system=REPLY_SYSTEM_PROMPT,
                user=f"用户请求: {message}\n\n执行步骤与结果:\n{obs_text}\n\n请生成回复。",
            )
        except Exception:
            return f"已完成。\n{obs_text}"

    async def _simple_reply(self, session: Session, message: str, context: str) -> str:
        try:
            history = session.history[-10:]
            messages = [
                {"role": "system", "content": "你是 FSAgent 智能办公助手。请友好地回答用户问题。"},
            ]
            if context:
                messages.append({"role": "system", "content": f"相关上下文:\n{context}"})
            messages.extend(history)

            result = await self.llm.chat(messages=messages)
            return result["choices"][0]["message"]["content"] or "收到，我理解了。"
        except Exception:
            return "收到，我理解了你的问题。"
