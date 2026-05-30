from __future__ import annotations

from fastapi import APIRouter

from common.utils import utc_now
from models.response import ResponseModel

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/health")
async def health_check() -> ResponseModel:
    return ResponseModel(
        data={
            "status": "healthy",
            "timestamp": utc_now().isoformat(),
        }
    )


@router.get("/metrics")
async def metrics() -> ResponseModel:
    return ResponseModel(
        data={
            "uptime": "ok",
            "sessions_active": 0,
            "skills_executed": 0,
            "errors_24h": 0,
        }
    )


@router.post("/cache/refresh")
async def refresh_cache() -> ResponseModel:
    return ResponseModel(message="Cache refresh triggered")
