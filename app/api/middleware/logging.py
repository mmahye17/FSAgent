from __future__ import annotations

import time

from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware

from common.logger import get_logger
from common.utils import generate_uuid

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = generate_uuid()
        request.state.request_id = request_id

        start = time.monotonic()
        response = await call_next(request)
        elapsed_ms = (time.monotonic() - start) * 1000

        logger.info(
            "request completed",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            elapsed_ms=round(elapsed_ms, 2),
        )

        response.headers["X-Request-ID"] = request_id
        return response


def setup_logging_middleware(app: FastAPI) -> None:
    app.add_middleware(RequestLoggingMiddleware)
