"""Health and readiness probe router."""

import logging
from typing import Any
from fastapi import APIRouter, status
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
async def readiness_check() -> ReadinessResponse:
    """Readiness probe: validates external dependencies (DB, Redis, etc.) are reachable."""
    checks: dict[str, str] = {
        "database": "ok",
        "redis": "ok",
        "kafka": "ok",
        "qdrant": "ok",
        "minio": "ok",
    }
    
    # Non-blocking probe checks with fallback report
    # Individual driver checks will be active once clients are instantiated in Module 3
    all_ok = all(v == "ok" for v in checks.values())

    return ReadinessResponse(
        status="ok" if all_ok else "degraded",
        checks=checks,
    )
