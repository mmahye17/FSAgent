from __future__ import annotations

from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ResponseModel(BaseModel, Generic[T]):
    code: int = Field(default=0, description="状态码，0 表示成功")
    message: str = Field(default="success", description="提示信息")
    data: T | None = Field(default=None, description="响应数据")
    request_id: str = Field(default="", description="请求 ID")


class PaginatedData(BaseModel, Generic[T]):
    items: list[T] = Field(default_factory=list)
    total: int = Field(default=0)
    page: int = Field(default=1)
    page_size: int = Field(default=20)


class ErrorResponse(BaseModel):
    code: int
    message: str
    detail: Any = None
    request_id: str = ""
    timestamp: datetime = Field(default_factory=datetime.now)
