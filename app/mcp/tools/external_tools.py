from __future__ import annotations

from typing import Any

from app.mcp.tools.base import MCPTool
from common.logger import get_logger

logger = get_logger(__name__)


class WebSearchTool(MCPTool):
    name = "external.web.search"
    description = "搜索网络信息"
    parameters = {
        "query": {"type": "string", "description": "搜索关键词"},
        "top_k": {"type": "integer", "description": "返回条数，默认 5"},
    }

    async def execute(self, **kwargs: Any) -> Any:
        return {"results": [], "note": "web search not configured"}


class JiraQueryTool(MCPTool):
    name = "external.jira.query"
    description = "查询 Jira Issue"
    parameters = {
        "jql": {"type": "string", "description": "JQL 查询语句"},
        "max_results": {"type": "integer", "description": "最大结果数，默认 10"},
    }

    async def execute(self, **kwargs: Any) -> Any:
        return {"issues": [], "note": "jira integration not configured"}


class GitHubPRTool(MCPTool):
    name = "external.github.pr"
    description = "查询 GitHub Pull Request 信息"
    parameters = {
        "owner": {"type": "string", "description": "仓库所有者"},
        "repo": {"type": "string", "description": "仓库名"},
        "pr_number": {"type": "integer", "description": "PR 编号"},
    }

    async def execute(self, **kwargs: Any) -> Any:
        return {"pr": {}, "note": "github integration not configured"}
