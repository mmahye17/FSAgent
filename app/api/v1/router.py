from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import admin, chat, mcp, session, skill, webhook

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(webhook.router)
api_router.include_router(chat.router)
api_router.include_router(session.router)
api_router.include_router(skill.router)
api_router.include_router(mcp.router)
api_router.include_router(admin.router)
