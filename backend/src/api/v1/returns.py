"""Return scoring endpoints."""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, Request

from src.api.middleware.auth import TokenData, verify_api_key, require_role
from src.api.middleware.rate_limit import rate_limit
from src.core.schemas.return_request import ReturnScoreRequest, ReturnScoreResponse, PolicyConfig
from src.services.return_scoring_service import ReturnScoringService
from src.db.models.tenant import Tenant

router = APIRouter(prefix="/returns", tags=["returns"])

async def get_return_scoring_service(request: Request) -> ReturnScoringService:
    # MVP mock. In a real app we would get the redis and model registry from request.app.state
    # return ReturnScoringService(request.app.state.redis, request.app.state.model_registry)
    from src.integrations.redis_client import RedisClient
    from src.ml.serving.model_registry import ModelRegistry
    return ReturnScoringService(RedisClient(), ModelRegistry())

async def get_tenant(token: TokenData = Depends(verify_api_key)) -> Tenant:
    # MVP mock. Default policy config
    policy = {
        "tenant_id": str(token.tenant_id),
        "low_threshold": 25,
        "medium_threshold": 50,
        "high_threshold": 75,
        "auto_deny_enabled": False,
        "high_value_customer_override": True
    }
    return Tenant(id=token.tenant_id, name="Test Tenant", policy_config=policy)

@router.post("/score", response_model=ReturnScoreResponse, dependencies=[Depends(rate_limit(100, 1))])
async def score_return(
    request: ReturnScoreRequest,
    tenant: Tenant = Depends(get_tenant),
    service: ReturnScoringService = Depends(get_return_scoring_service)
):
    """
    Score the risk of a new return initiation in real-time.
    Secured by API Key.
    """
    try:
        response = await service.score(request, tenant)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history")
async def get_return_history(
    token: TokenData = Depends(require_role("analyst", "admin")),
    customer_id: str | None = None,
    risk_tier: str | None = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100)
):
    """
    Paginated history of return scoring decisions.
    Secured by JWT.
    """
    # MVP stub: usually calls a database repository
    return {"items": [], "total": 0, "page": page, "size": size}

@router.put("/policy")
async def update_return_policy(
    policy: PolicyConfig,
    token: TokenData = Depends(require_role("admin"))
):
    """
    Update merchant risk thresholds.
    Secured by JWT, Admin only.
    """
    if not (policy.low_threshold < policy.medium_threshold < policy.high_threshold):
        raise HTTPException(status_code=400, detail="Invalid thresholds: must be low < medium < high")
        
    # MVP stub: would update tenant record in database
    return {"status": "success", "message": "Policy updated successfully"}
