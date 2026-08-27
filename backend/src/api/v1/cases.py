"""Case management endpoints."""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from src.api.middleware.auth import TokenData, require_role
from src.services.case_management_service import CaseManagementService
from src.core.enums import CaseStatus

router = APIRouter(prefix="/cases", tags=["cases"])

async def get_case_service() -> CaseManagementService:
    from src.db.repositories.case_repository import CaseRepository
    return CaseManagementService(CaseRepository(None))

@router.get("")
async def search_cases(
    token: TokenData = Depends(require_role("analyst", "admin")),
    service: CaseManagementService = Depends(get_case_service),
    query: str = "",
    status: CaseStatus | None = None,
    source: str | None = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100)
):
    """
    List all cases with filters and pagination.
    """
    try:
        filters = {}
        if status:
            filters["status"] = status
        if source:
            filters["source"] = source
            
        cases, total = await service.search(token.tenant_id, query, filters, page, size)
        return {"items": cases, "total": total, "page": page, "size": size}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_dashboard_stats(
    token: TokenData = Depends(require_role("analyst", "admin")),
    service: CaseManagementService = Depends(get_case_service)
):
    """
    Dashboard statistics (counts by status, priority, win rate).
    """
    try:
        stats = await service.get_dashboard_stats(token.tenant_id)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class AssignRequest(BaseModel):
    user_id: UUID

@router.patch("/{case_id}/assign")
async def assign_case(
    case_id: UUID,
    request: AssignRequest,
    token: TokenData = Depends(require_role("analyst", "admin")),
    service: CaseManagementService = Depends(get_case_service)
):
    """
    Assign a case to an analyst.
    """
    try:
        await service.assign(case_id, token.tenant_id, request.user_id, token.user_id)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class StatusUpdateRequest(BaseModel):
    status: CaseStatus
    resolution: str | None = None

@router.patch("/{case_id}/status")
async def update_case_status(
    case_id: UUID,
    request: StatusUpdateRequest,
    token: TokenData = Depends(require_role("analyst", "admin")),
    service: CaseManagementService = Depends(get_case_service)
):
    """
    Update case status.
    """
    try:
        await service.update_status(case_id, token.tenant_id, request.status, token.user_id, request.resolution)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
