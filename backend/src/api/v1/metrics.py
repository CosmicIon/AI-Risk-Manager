"""Metrics and evaluation endpoints."""

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from src.api.middleware.auth import TokenData, require_role

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/prometheus", response_class=PlainTextResponse)
async def get_prometheus_metrics():
    """
    Scraping endpoint for Prometheus.
    """
    # Exposes metrics registered via prometheus_client
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@router.get("/evaluation/{model_name}/latest")
async def get_latest_evaluation(
    model_name: str, token: TokenData = Depends(require_role("admin", "data_scientist"))
):
    """
    Get the latest evaluation report for a model.
    """
    # MVP stub
    if model_name == "return_risk":
        return {
            "model_name": model_name,
            "f1_score": 0.92,
            "roc_auc": 0.96,
            "cost_weighted_loss": 12.5,
            "evaluated_at": "2024-12-01T00:00:00Z",
        }
    raise HTTPException(status_code=404, detail="Model not found")


@router.get("/cost-summary")
async def get_cost_summary(token: TokenData = Depends(require_role("admin"))):
    """
    ₹-denominated cost summary for dashboard metrics.
    """
    # MVP stub
    return {
        "total_fp_cost": Decimal("4500.00"),
        "total_fn_cost": Decimal("12500.00"),
        "total_savings": Decimal("85000.00"),
        "period": "last_30_days",
        "currency": "INR",
    }
