from __future__ import annotations

from app.mcp.registry import mcp_tool_registry
from common.logger import get_logger

logger = get_logger(__name__)


class MCPServer:
    """MCP Server 包装器，提供标准 MCP 协议接口。"""

    def __init__(self) -> None:
        self.registry = mcp_tool_registry

    async def list_tools(self) -> list[dict]:
        return self.registry.list_tools()

    async def call_tool(self, name: str, arguments: dict) -> dict:
        try:
            result = await self.registry.call(name, **arguments)
            return {
                "content": [{"type": "text", "text": str(result)}],
                "isError": False,
            }
        except Exception as exc:
            return {
                "content": [{"type": "text", "text": str(exc)}],
                "isError": True,
            }

    async def handle_request(self, method: str, params: dict | None = None) -> dict:
        params = params or {}
        if method == "tools/list":
            return {"tools": await self.list_tools()}
        elif method == "tools/call":
            return await self.call_tool(params["name"], params.get("arguments", {}))
        else:
            return {"error": f"Unknown method: {method}"}


mcp_server = MCPServer()
