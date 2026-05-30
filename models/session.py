from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from common.utils import generate_id, utc_now

SessionStatus = Literal["active", "idle", "expired", "closed"]


class SessionCreate(BaseModel):
    user_id: str
    platform: str = "api"
    group_id: str | None = None
    tenant_id: str | None = None
    metadata: dict[str, str] | None = None


class SessionInfo(BaseModel):
    session_id: str = Field(default_factory=generate_id)
    user_id: str
    platform: str
    group_id: str | None = None
    tenant_id: str | None = None
    status: SessionStatus = "active"
    message_count: int = 0
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    expires_at: datetime | None = None
    metadata: dict[str, str] | None = None


class SessionMessage(BaseModel):
    message_id: str = Field(default_factory=generate_id)
    session_id: str
    role: str
    content: str
    tool_calls: list[dict] | None = None
    created_at: datetime = Field(default_factory=utc_now)
