from __future__ import annotations

from enum import Enum

from common.llm import get_llm_client
from common.logger import get_logger

logger = get_logger(__name__)


class IntentType(str, Enum):
    MEETING_BOOK = "meeting_book"
    CALENDAR_QUERY = "calendar_query"
    MINUTES_GENERATE = "minutes_generate"
    PROGRESS_TRACK = "progress_track"
    WEEKLY_REPORT = "weekly_report"
    KNOWLEDGE_QA = "knowledge_qa"
    GENERAL_CHAT = "general_chat"
    UNKNOWN = "unknown"


INTENT_SYSTEM_PROMPT = """你是一个意图识别助手。分析用户输入，判断意图类型。

意图类型:
- meeting_book: 预定会议、约时间、安排会议
- calendar_query: 查询日程、查看忙闲、今天有什么安排
- minutes_generate: 生成会议纪要、整理会议记录、总结会议
- progress_track: 追踪进度、查询任务状态、上次说的xxx怎么样了
- weekly_report: 生成周报、本周总结、上周回顾
- knowledge_qa: 知识问答、查询文档、wiki查询
- general_chat: 闲聊、简单问答、无法归类的问题

请只输出意图类型，不要输出其他内容。"""


class IntentRecognizer:
    def __init__(self) -> None:
        self.llm = get_llm_client()

    async def recognize(self, text: str) -> IntentType:
        try:
            result = await self.llm.simple_prompt(
                system=INTENT_SYSTEM_PROMPT,
                user=text,
            )
            raw = result.strip().lower()
            return IntentType(raw)
        except ValueError:
            logger.warning("未识别到意图", text=text[:100])
            return IntentType.UNKNOWN
        except Exception:
            return IntentType.GENERAL_CHAT

    def quick_match(self, text: str) -> IntentType:
        text_lower = text.lower()

        keywords = {
            IntentType.MEETING_BOOK: ["约", "预定", "会议", "开会", "安排", "邀请", "拉上"],
            IntentType.CALENDAR_QUERY: ["日程", "忙闲", "今天有什么", "安排", "空闲"],
            IntentType.MINUTES_GENERATE: ["纪要", "会议记录", "总结", "妙记", "刚才的"],
            IntentType.PROGRESS_TRACK: ["进度", "上次", "之前说", "怎么样了", "状态"],
            IntentType.WEEKLY_REPORT: ["周报", "本周", "上周", "日报"],
            IntentType.KNOWLEDGE_QA: ["什么是", "怎么", "如何", "文档", "wiki", "知道"],
        }

        for intent, words in keywords.items():
            if any(w in text_lower for w in words):
                return intent

        return IntentType.GENERAL_CHAT
