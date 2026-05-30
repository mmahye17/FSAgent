from __future__ import annotations

from datetime import datetime
from typing import Any

from app.mcp.tools.base import MCPTool
from common.llm import get_llm_client
from common.logger import get_logger

logger = get_logger(__name__)


class LLMCallTool(MCPTool):
    name = "common.llm.call"
    description = "调用 LLM 进行文本生成"
    parameters = {
        "system": {"type": "string", "description": "系统提示词"},
        "user": {"type": "string", "description": "用户输入"},
        "model": {"type": "string", "description": "模型名称，可选"},
    }

    async def execute(self, **kwargs: Any) -> Any:
        client = get_llm_client()
        return await client.simple_prompt(
            system=kwargs["system"],
            user=kwargs["user"],
            model=kwargs.get("model"),
        )


class CurrentTimeTool(MCPTool):
    name = "common.time.now"
    description = "获取当前时间"
    parameters = {}

    async def execute(self, **kwargs: Any) -> Any:
        now = datetime.now()
        return {
            "iso": now.isoformat(),
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "weekday": now.strftime("%A"),
            "timestamp": int(now.timestamp()),
        }


class TextTruncateTool(MCPTool):
    name = "common.text.truncate"
    description = "截断文本到指定长度"
    parameters = {
        "text": {"type": "string", "description": "输入文本"},
        "max_length": {"type": "integer", "description": "最大长度，默认 2000"},
    }

    async def execute(self, **kwargs: Any) -> Any:
        from common.utils import truncate_text

        return truncate_text(kwargs["text"], kwargs.get("max_length", 2000))
