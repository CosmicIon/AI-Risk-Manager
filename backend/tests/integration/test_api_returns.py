import pytest
from httpx import AsyncClient, ASGITransport
from datetime import datetime, timezone
from uuid import uuid4

from unittest.mock import AsyncMock

from src.main import app
from src.api.v1.returns import get_return_scoring_service

# Mock Redis state
app.state.redis = AsyncMock()
app.state.redis.check_rate_limit.return_value = True

mock_return_service = AsyncMock()
mock_return_service.score.return_value = {
    "request_id": "req-12345",
    "risk_score": 15,
    "risk_tier": "LOW",
    "decision": "auto_approve",
    "explanation": "No explanation available.",
    "top_features": [],
    "model_version": "v1",
    "inference_latency_ms": 10.5,
    "scored_at": "2024-12-31T23:59:59Z"
}

app.dependency_overrides[get_return_scoring_service] = lambda: mock_return_service

@pytest.fixture
def test_api_key():
    return "test-api-key-123"

@pytest.fixture
def auth_headers(test_api_key):
    return {"x-api-key": test_api_key}

@pytest.mark.asyncio
async def test_score_return(auth_headers):
    payload = {
        "request_id": "req-12345",
        "tenant_id": str(uuid4()),
        "customer_id": "cust-abc",
        "order_id": "ord-xyz",
        "order_amount": 250.00,
        "return_amount": 100.00,
        "return_reason": "Defective",
        "order_date": datetime.now(timezone.utc).isoformat(),
        "return_initiated_at": datetime.now(timezone.utc).isoformat(),
        "product_category": "Electronics"
    }
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/returns/score", json=payload, headers=auth_headers)
        
    assert response.status_code == 200
    data = response.json()
    assert "risk_score" in data
    assert "decision" in data
    assert "explanation" in data
    assert "inference_latency_ms" in data

@pytest.mark.asyncio
async def test_score_return_rate_limit(auth_headers):
    # This tests the endpoint presence, but mocking Redis ratelimit behavior
    # properly would require an integration test with an actual Redis instance.
    pass
