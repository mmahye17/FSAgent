from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from common.utils import generate_uuid

MessageRole = Literal["user", "assistant", "system", "tool"]


class ChatMessage(BaseModel):
    role: MessageRole
    content: str
    name: str | None = None
    tool_calls: list[dict] | None = None
    tool_call_id: str | None = None


class ChatRequest(BaseModel):
    session_id: str | None = Field(default=None, description="会话 ID，不传则新建会话")
    message: str = Field(..., min_length=1, max_length=10000)
    platform: Literal["feishu", "wechat", "api"] = Field(default="api")
    user_id: str = Field(..., description="用户标识")
    group_id: str | None = Field(default=None, description="群组标识")
    metadata: dict[str, str] | None = Field(default=None)


class ChatResponse(BaseModel):
    session_id: str
    message_id: str = Field(default_factory=generate_uuid)
    reply: str
    tool_calls_made: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)


class AsyncChatResponse(BaseModel):
    task_id: str
    session_id: str
    status: Literal["queued", "processing", "completed", "failed"] = "queued"


class TaskStatus(BaseModel):
    task_id: str
    status: Literal["queued", "processing", "completed", "failed"]
    result: ChatResponse | None = None
    error: str | None = None
    created_at: datetime
    updated_at: datetime
