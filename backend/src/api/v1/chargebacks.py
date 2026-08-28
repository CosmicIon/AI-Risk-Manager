"""Chargeback ingestion and review endpoints."""

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from src.api.middleware.auth import TokenData, require_role, verify_api_key
from src.api.middleware.rate_limit import rate_limit
from src.core.schemas.chargeback import ChargebackIngestRequest, ChargebackIngestResponse
from src.db.models.tenant import Tenant
from src.services.chargeback_service import ChargebackService

# For MVP, we mock tenant retrieval and dependency injection.
# In a real app, we'd use Depends(get_tenant) and Depends(get_chargeback_service).

router = APIRouter(prefix="/chargebacks", tags=["chargebacks"])


async def get_chargeback_service() -> ChargebackService:
    # Mock dependency resolution
    from src.db.repositories.case_repo import CaseRepository
    from src.db.repositories.chargeback_repo import ChargebackRepository
    from src.services.chargeback_service import ChargebackService

    # In reality, this would be injected with real async DB sessions
    return ChargebackService(ChargebackRepository(None), CaseRepository(None), None)  # type: ignore


async def get_tenant(token: TokenData = Depends(verify_api_key)) -> Tenant:
    # Mock tenant retrieval based on token payload
    return Tenant(id=token.tenant_id, name="Test Tenant", policy_config={})


@router.post(
    "/ingest",
    response_model=ChargebackIngestResponse,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(rate_limit(500, 1))],
)
async def ingest_chargeback(
    request: ChargebackIngestRequest,
    tenant: Tenant = Depends(get_tenant),
    service: ChargebackService = Depends(get_chargeback_service),
):
    """
    Ingest a new chargeback notification (webhook from PSP).
    Secured by API Key.
    """
    try:
        response = await service.ingest(request, tenant, session=None)
        return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/pending")
async def get_pending_reviews(
    token: TokenData = Depends(require_role("analyst", "admin")),
    service: ChargebackService = Depends(get_chargeback_service),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    """
    Get cases with status DRAFT_READY for review.
    Secured by JWT.
    """
    try:
        cases = await service.get_pending_reviews(token.tenant_id)
        # Apply rudimentary pagination
        start = (page - 1) * size
        end = start + size
        return {"items": cases[start:end], "total": len(cases), "page": page, "size": size}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


class ReviewRequest(BaseModel):
    action: Literal["approve", "edit", "reject"]
    edits: dict | None = None


@router.post("/{case_id}/review")
async def review_chargeback(
    case_id: UUID,
    request: ReviewRequest,
    token: TokenData = Depends(require_role("analyst", "admin")),
    service: ChargebackService = Depends(get_chargeback_service),
):
    """
    Submit a review action on a chargeback representment draft.
    """
    try:
        await service.review(
            case_id,
            token.tenant_id,
            request.action,
            request.edits or {},
            token.user_id,
            session=None,
        )
        return {"status": "success", "message": f"Action '{request.action}' processed"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
