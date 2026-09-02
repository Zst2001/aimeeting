import logging
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.health import router as health_router
from app.core.config import get_settings
from app.core.error_codes import SYSTEM_INTERNAL_ERROR
from app.core.exceptions import AppException
from app.core.logging import configure_logging, request_id_context


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging()
    app = FastAPI(title=settings.app_name, version="0.1.0")
    logger = logging.getLogger(__name__)

    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):  # type: ignore[no-untyped-def]
        request_id = request.headers.get("X-Request-ID") or f"req_{uuid4().hex}"
        token = request_id_context.set(request_id)
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            request_id_context.reset(token)

    @app.exception_handler(AppException)
    async def app_exception_handler(_: Request, exc: AppException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "code": exc.code,
                "message": exc.message,
                "data": None,
                "request_id": request_id_context.get(),
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled application error", exc_info=exc)
        return JSONResponse(
            status_code=500,
            content={
                "code": SYSTEM_INTERNAL_ERROR,
                "message": "系统内部错误",
                "data": None,
                "request_id": request_id_context.get(),
            },
        )

    app.include_router(health_router)
    return app


app = create_app()
