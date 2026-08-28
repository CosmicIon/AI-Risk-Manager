from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.core.enums import CaseStatus
from src.core.schemas.return_request import ReturnScoreRequest
from src.db.models.tenant import Tenant
from src.services.case_management_service import CaseManagementService
from src.services.fraud_detection_service import FraudDetectionService
from src.services.return_scoring_service import ReturnScoringService


@pytest.fixture
def mock_redis():
    redis = AsyncMock()
    redis.get_feature_vector.return_value = {
        "return_count_30d": 1.0,
        "return_amount_total_30d": 50.0,
    }
    return redis


@pytest.fixture
def mock_model_registry():
    registry = MagicMock()
    model = MagicMock()
    # Return a low risk probability
    model.predict_with_latency.return_value = ([0.15], 5)
    registry.get_model.return_value = model
    return registry


@pytest.fixture
def tenant():
    return Tenant(
        id=uuid4(),
        name="Test Merchant",
        policy_config={
            "tenant_id": str(uuid4()),
            "auto_deny_enabled": True,
            "high_threshold": 80,
            "medium_threshold": 50,
            "low_threshold": 20,
            "high_value_customer_override": True,
        },
    )


@pytest.mark.asyncio
async def test_return_scoring_service_low_risk(mock_redis, mock_model_registry, tenant):
    service = ReturnScoringService(mock_redis, mock_model_registry)
    req = ReturnScoreRequest(
        request_id="req-123",
        tenant_id=tenant.id,
        customer_id="cust-123",
        order_id="ord-123",
        order_amount=10.0,
        return_amount=10.0,
        return_reason="Defective",
        order_date=datetime.now(UTC),
        return_initiated_at=datetime.now(UTC),
        product_category="Electronics",
        items=[{"item_id": "item-1", "amount": 10.0, "reason": "Defective"}],
    )

    response = await service.score(req, tenant)

    assert response.risk_score == 15
    assert response.decision == "auto_approve"


@pytest.mark.asyncio
async def test_return_scoring_service_high_risk_override(mock_redis, mock_model_registry, tenant):
    # Setup mock to return high probability (0.95 -> score 95)
    model = MagicMock()
    model.predict_with_latency.return_value = ([0.95], 5)
    mock_model_registry.get_model.return_value = model

    # Setup mock redis to return high LTV to trigger override
    mock_redis.get_feature_vector.return_value = {"customer_lifetime_value": 6000.0}

    service = ReturnScoringService(mock_redis, mock_model_registry)
    req = ReturnScoreRequest(
        request_id="req-124",
        tenant_id=tenant.id,
        customer_id="cust-high-ltv",
        order_id="ord-124",
        order_amount=100.0,
        return_amount=100.0,
        return_reason="Wrong Size",
        order_date=datetime.now(UTC),
        return_initiated_at=datetime.now(UTC),
        product_category="Clothing",
        items=[{"item_id": "item-2", "amount": 100.0, "reason": "Wrong Size"}],
    )

    response = await service.score(req, tenant)

    assert response.risk_score == 95
    # Since high_value_customer_override is True and LTV > 5000, it should override auto_deny to manual_review
    assert response.decision == "manual_review"


@pytest.mark.asyncio
async def test_fraud_detection_service_alert_routing(tenant):
    mock_case_repo = AsyncMock()
    mock_kafka = AsyncMock()
    mock_notif = AsyncMock()

    service = FraudDetectionService(mock_case_repo, mock_kafka, mock_notif)

    alert = {"alert_id": "alert-1", "severity": "CRITICAL", "anomaly_type": "Velocity Spike"}

    await service.handle_alert(alert, tenant, MagicMock())

    assert mock_case_repo.create.called
    assert mock_notif.route_alert.called


@pytest.mark.asyncio
async def test_case_management_service_state_machine():
    mock_repo = AsyncMock()

    # Setup mock case
    mock_case = MagicMock()
    mock_case.status = CaseStatus.LOST
    mock_repo.get_by_id.return_value = mock_case

    service = CaseManagementService(mock_repo)

    with pytest.raises(ValueError, match="Cannot transition from terminal state"):
        await service.update_status(uuid4(), uuid4(), CaseStatus.DRAFT_READY, uuid4(), MagicMock())
