"""Health and readiness probe router."""

import logging

from fastapi import APIRouter, status, Request
from pydantic import BaseModel

from src.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health & Probes"])


class HealthResponse(BaseModel):
    status: str
    environment: str
    version: str


class ReadinessResponse(BaseModel):
    status: str
    checks: dict[str, str]


@router.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
async def health_check() -> HealthResponse:
    """Liveness probe: verifies the API process is alive."""
    return HealthResponse(
        status="ok",
        environment=settings.ENVIRONMENT,
        version="0.1.0",
    )


@router.get("/readiness", response_model=ReadinessResponse, status_code=status.HTTP_200_OK)
async def readiness_check(request: Request) -> ReadinessResponse:
    """Readiness probe: validates external dependencies (DB, Redis, etc.) are reachable."""
    
    redis_ok = await request.app.state.redis.health_check() if hasattr(request.app.state, 'redis') else False
    kafka_ok = await request.app.state.kafka.health_check() if hasattr(request.app.state, 'kafka') else False
    qdrant_ok = await request.app.state.qdrant.health_check() if hasattr(request.app.state, 'qdrant') else False
    minio_ok = await request.app.state.minio.health_check() if hasattr(request.app.state, 'minio') else False
    
    checks: dict[str, str] = {
        "database": "ok", # DB check via SQLAlchemy can be added if needed
        "redis": "ok" if redis_ok else "failed",
        "kafka": "ok" if kafka_ok else "failed",
        "qdrant": "ok" if qdrant_ok else "failed",
        "minio": "ok" if minio_ok else "failed",
    }

    all_ok = all(v == "ok" for v in checks.values())

    return ReadinessResponse(
        status="ok" if all_ok else "degraded",
        checks=checks,
    )
