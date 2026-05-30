from __future__ import annotations

from typing import Any

from app.mcp.tools.base import MCPTool
from app.mcp.tools.common_tools import CurrentTimeTool, LLMCallTool, TextTruncateTool
from app.mcp.tools.external_tools import GitHubPRTool, JiraQueryTool, WebSearchTool
from app.mcp.tools.feishu_tools import (
    FeishuCalendarCreateTool,
    FeishuCalendarQueryTool,
    FeishuDocContentTool,
    FeishuGroupCreateTool,
    FeishuMinutesTranscriptTool,
    FeishuSendMessageTool,
    FeishuUserQueryTool,
)
from common.logger import get_logger

logger = get_logger(__name__)


class MCPToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, MCPTool] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        defaults: list[MCPTool] = [
            FeishuSendMessageTool(),
            FeishuCalendarQueryTool(),
            FeishuCalendarCreateTool(),
            FeishuGroupCreateTool(),
            FeishuUserQueryTool(),
            FeishuDocContentTool(),
            FeishuMinutesTranscriptTool(),
            LLMCallTool(),
            CurrentTimeTool(),
            TextTruncateTool(),
            WebSearchTool(),
            JiraQueryTool(),
            GitHubPRTool(),
        ]
        for tool in defaults:
            self.register(tool)

    def register(self, tool: MCPTool) -> None:
        self._tools[tool.name] = tool
        logger.debug("mcp_tool_registered", name=tool.name)

    def get(self, name: str) -> MCPTool | None:
        return self._tools.get(name)

    async def call(self, name: str, **kwargs: Any) -> Any:
        tool = self._tools.get(name)
        if not tool:
            raise KeyError(f"Tool '{name}' not found")
        logger.info("mcp_tool_calling", name=name)
        return await tool.execute(**kwargs)

    def list_tools(self) -> list[dict[str, Any]]:
        return [tool.to_schema() for tool in self._tools.values()]


mcp_tool_registry = MCPToolRegistry()
