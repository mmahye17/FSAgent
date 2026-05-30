from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.middleware.cors import setup_cors
from app.api.middleware.logging import setup_logging_middleware
from app.api.middleware.ratelimit import setup_rate_limit
from app.api.v1.router import api_router
from app.config import get_settings
from common.errors import FSAgentError
from common.logger import get_logger, setup_logging
from models.response import ErrorResponse

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    setup_logging(settings.LOG_LEVEL, json_format=not settings.DEBUG)
    logger.info("FSAgent后端启动", env=settings.APP_ENV)
    yield
    logger.info("FSAgent后端关闭")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        description="FSAgent - 飞书/微信智能办公助手 Agent",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
    )

    setup_cors(app)
    setup_logging_middleware(app)
    setup_rate_limit(app)

    app.include_router(api_router)

    @app.exception_handler(FSAgentError)
    async def fsagent_error_handler(request: Request, exc: FSAgentError) -> JSONResponse:
        request_id = getattr(request.state, "request_id", "")
        return JSONResponse(
            status_code=exc.code if exc.code < 500 else 500,
            content=ErrorResponse(
                code=exc.code,
                message=exc.message,
                detail=exc.detail,
                request_id=request_id,
            ).model_dump(),
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        request_id = getattr(request.state, "request_id", "")
        logger.error("unhandled_error", error=str(exc), request_id=request_id)
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                code=500,
                message="Internal server error",
                detail=str(exc) if settings.DEBUG else None,
                request_id=request_id,
            ).model_dump(),
        )

    return app


app = create_app()


def main() -> None:
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )


if __name__ == "__main__":
    main()
