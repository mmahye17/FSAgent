from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SkillParameter(BaseModel):
    name: str
    type: str = "string"
    description: str = ""
    required: bool = False
    default: Any = None
    enum: list[str] | None = None


class SkillDefinition(BaseModel):
    name: str = Field(..., description="技能唯一标识，如 meeting.book")
    display_name: str = Field(..., description="展示名称")
    description: str = Field(..., description="技能描述")
    parameters: list[SkillParameter] = Field(default_factory=list)
    category: str = Field(default="general")
    requires_confirmation: bool = Field(default=False)


class SkillExecuteRequest(BaseModel):
    parameters: dict[str, Any] = Field(default_factory=dict)
    session_id: str | None = None


class SkillResult(BaseModel):
    success: bool
    skill_name: str
    result: Any = None
    error: str | None = None
    execution_time_ms: float = 0


class SkillListResponse(BaseModel):
    skills: list[SkillDefinition]
