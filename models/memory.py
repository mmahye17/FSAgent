from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from common.utils import generate_id, utc_now


class MemoryEntry(BaseModel):
    memory_id: str = Field(default_factory=generate_id)
    session_id: str | None = None
    user_id: str
    content: str
    memory_type: Literal["working", "episodic", "semantic"] = "working"
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    embedding: list[float] | None = None
    metadata: dict[str, str] | None = None
    created_at: datetime = Field(default_factory=utc_now)
    ttl_seconds: int | None = None


class MemorySearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    memory_type: Literal["working", "episodic", "semantic"] | None = None
    user_id: str | None = None
    top_k: int = Field(default=10, ge=1, le=100)
    min_score: float = Field(default=0.5, ge=0.0, le=1.0)


class MemorySearchResult(BaseModel):
    memory_id: str
    content: str
    score: float
    memory_type: str
    metadata: dict[str, str] | None = None
    created_at: datetime | None = None
