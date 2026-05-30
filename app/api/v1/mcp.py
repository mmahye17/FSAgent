from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from app.mcp.registry import mcp_tool_registry
from models.response import ResponseModel

router = APIRouter(prefix="/mcp", tags=["mcp"])


@router.get("/tools", response_model=ResponseModel[list[dict[str, Any]]])
async def list_tools() -> ResponseModel[list[dict[str, Any]]]:
    tools = mcp_tool_registry.list_tools()
    return ResponseModel(data=tools)


@router.post("/tools/{tool_name}/call", response_model=ResponseModel)
async def call_tool(tool_name: str, body: dict[str, Any] | None = None) -> ResponseModel:
    body = body or {}
    params = body.get("arguments", body)

    try:
        result = await mcp_tool_registry.call(tool_name, **params)
        return ResponseModel(data=result)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
