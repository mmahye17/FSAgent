from __future__ import annotations

from fastapi import FastAPI, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import get_settings

limiter = Limiter(key_func=get_remote_address)


def setup_rate_limit(app: FastAPI) -> None:
    settings = get_settings()
    if not settings.RATE_LIMIT_ENABLED:
        return

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
