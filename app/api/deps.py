from __future__ import annotations

from collections.abc import AsyncGenerator

from fastapi import Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db_session


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_db_session():
        yield session


async def get_request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "")


async def verify_webhook_auth(
    request: Request,
    x_api_key: str = Header(default="", alias="X-API-Key"),
) -> None:
    from app.config import get_settings

    settings = get_settings()
    path = request.url.path

    if "feishu" in path or "wechat" in path:
        return

    if x_api_key and x_api_key == settings.JWT_SECRET_KEY:
        return

    raise HTTPException(status_code=401, detail="Unauthorized")
