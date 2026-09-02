import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from redis import Redis
from sqlalchemy import text

from app.core.config import get_settings
from app.db.session import engine


router = APIRouter(tags=["health"])
logger = logging.getLogger(__name__)


def check_mysql() -> None:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))


def check_redis() -> None:
    redis_client = Redis.from_url(get_settings().redis_url, decode_responses=True)
    try:
        redis_client.ping()
    finally:
        redis_client.close()


@router.get("/health")
def health() -> dict[str, str]:
    """Liveness probe: only confirms that the FastAPI process is running."""

    return {"status": "ok"}


@router.get("/ready")
def ready() -> JSONResponse:
    """Readiness probe: verify MySQL and Redis without exposing connection details."""

    components: dict[str, str] = {}
    checks = {"mysql": check_mysql, "redis": check_redis}

    for component, check in checks.items():
        try:
            check()
            components[component] = "ok"
        except Exception:
            logger.exception("Readiness component check failed: %s", component)
            components[component] = "error"

    if all(status == "ok" for status in components.values()):
        return JSONResponse(status_code=200, content={"status": "ready", "components": components})

    return JSONResponse(status_code=503, content={"status": "not_ready", "components": components})
