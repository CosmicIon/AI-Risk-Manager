"""Fraud detection and anomaly endpoints."""

from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from src.api.middleware.auth import TokenData, require_role
from src.services.fraud_detection_service import FraudDetectionService

router = APIRouter(prefix="/fraud", tags=["fraud"])

async def get_fraud_service() -> FraudDetectionService:
    from src.db.repositories.case_repository import CaseRepository
    from src.services.notification_service import NotificationService
    return FraudDetectionService(CaseRepository(None), None, NotificationService())

@router.get("/alerts")
async def get_active_alerts(
    token: TokenData = Depends(require_role("analyst", "admin")),
    service: FraudDetectionService = Depends(get_fraud_service),
    severity: str | None = None,
    classification: str | None = None
):
    """
    List active fraud anomaly alerts for a tenant.
    Secured by JWT.
    """
    try:
        alerts = await service.get_active_alerts(token.tenant_id)
        # Apply filters in-memory for MVP (usually DB-side)
        if severity:
            alerts = [a for a in alerts if a.get("severity") == severity]
        if classification:
            alerts = [a for a in alerts if a.get("anomaly_type") == classification]
        return {"items": alerts, "total": len(alerts)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class KnownEventRequest(BaseModel):
    name: str
    start: datetime
    end: datetime
    threshold_multiplier: float = 2.0

@router.post("/events")
async def register_event(
    request: KnownEventRequest,
    token: TokenData = Depends(require_role("admin")),
    service: FraudDetectionService = Depends(get_fraud_service)
):
    """
    Register a known calendar event (e.g. Big Billion Days) to suppress false positives.
    Secured by JWT, Admin only.
    """
    try:
        await service.register_event(token.tenant_id, request.name, request.start, request.end)
        return {"status": "success", "message": f"Event '{request.name}' registered."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    token: TokenData = Depends(require_role("analyst", "admin"))
):
    """
    Mark an alert as acknowledged.
    """
    # MVP stub
    return {"status": "success", "message": f"Alert {alert_id} acknowledged"}
