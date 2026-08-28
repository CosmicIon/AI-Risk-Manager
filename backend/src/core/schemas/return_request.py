"""Return request and scoring schemas."""

from datetime import datetime
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from src.core.enums import RiskTier


class ReturnScoreRequest(BaseModel):
    """Request payload to score the risk of a new return initiation."""

    request_id: str
    tenant_id: UUID
    customer_id: str
    order_id: str
    order_amount: Decimal
    return_amount: Decimal
    return_reason: str
    order_date: datetime
    return_initiated_at: datetime
    product_category: str
    device_fingerprint: str | None = None
    ip_address: str | None = None

    @field_validator("return_amount")
    @classmethod
    def validate_return_amount(cls, v: Decimal, info) -> Decimal:
        """Ensure return amount does not exceed original order amount."""
        if "order_amount" in info.data and v > info.data["order_amount"]:
            raise ValueError("return_amount cannot exceed order_amount")
        return v


class FeatureVector(BaseModel):
    """Machine learning feature vector retrieved from the feature store."""

    customer_id: str
    features: dict[str, float]
    computed_at: datetime
    staleness_seconds: float
    is_degraded: bool = False


class ReturnScoreResponse(BaseModel):
    """Risk score and policy decision for a return request."""

    request_id: str
    risk_score: int = Field(ge=0, le=100)
    risk_tier: RiskTier
    decision: Literal["auto_approve", "manual_review", "auto_deny"]
    explanation: str
    top_features: list[dict[str, Any]]
    model_version: str
    inference_latency_ms: float
    scored_at: datetime

    @field_validator("risk_score", mode="before")
    @classmethod
    def clamp_risk_score(cls, v: int | float) -> int:
        """Clamp risk score to [0, 100]."""
        return max(0, min(100, int(v)))


class PolicyConfig(BaseModel):
    """Merchant-specific return policy configuration."""

    tenant_id: UUID
    low_threshold: int = 25
    medium_threshold: int = 50
    high_threshold: int = 75
    auto_deny_enabled: bool = False
    high_value_customer_override: bool = True
