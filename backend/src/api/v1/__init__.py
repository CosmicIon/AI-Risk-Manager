"""API v1 routers."""

from src.api.v1.cases import router as cases_router
from src.api.v1.chargebacks import router as chargebacks_router
from src.api.v1.fraud import router as fraud_router
from src.api.v1.health import router as health_router
from src.api.v1.metrics import router as metrics_router
from src.api.v1.returns import router as returns_router

__all__ = [
    "chargebacks_router",
    "returns_router",
    "fraud_router",
    "cases_router",
    "metrics_router",
    "health_router",
]
