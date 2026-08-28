from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from src.api.middleware.auth import create_access_token
from src.api.v1.chargebacks import get_chargeback_service
from src.core.enums import CaseStatus
from src.main import app

# Mock Redis state
app.state.redis = AsyncMock()
app.state.redis.check_rate_limit.return_value = True


mock_chargeback_service = AsyncMock()
mock_chargeback_service.ingest.return_value = {
    "case_id": "00000000-0000-0000-0000-000000000000",
    "deadline": "2024-12-31T23:59:59Z",
    "status": CaseStatus.NEW,
    "message": "ingested",
}
mock_chargeback_service.get_pending_reviews.return_value = [{"case_id": "CASE-1"}]

app.dependency_overrides[get_chargeback_service] = lambda: mock_chargeback_service


@pytest.fixture
def test_api_key():
    return "test-api-key-123"


@pytest.fixture
def auth_headers(test_api_key):
    return {"x-api-key": test_api_key}


@pytest.mark.asyncio
async def test_ingest_chargeback(auth_headers):
    payload = {
        "raw_payload": {"tenant_id": str(uuid4()), "network_arn": "ARN-123456", "amount": 100.50}
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/chargebacks/ingest", json=payload, headers=auth_headers)

    assert response.status_code == 202
    data = response.json()
    assert "case_id" in data
    assert "deadline" in data
    assert data["status"] == "NEW"


@pytest.mark.asyncio
async def test_get_pending_reviews():
    # Test JWT auth
    token = create_access_token(user_id=uuid4(), tenant_id=uuid4(), role="analyst")
    headers = {"Authorization": f"Bearer {token}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/chargebacks/pending", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert "items" in data


@pytest.mark.asyncio
async def test_unauthorized_access():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Missing API Key
        response = await ac.post("/api/v1/chargebacks/ingest", json={})
    assert response.status_code == 401
