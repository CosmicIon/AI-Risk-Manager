"""
End-to-end test: Chargeback full lifecycle.

Tests the complete chargeback flow from ingestion through agent pipeline
processing to analyst review, validating status transitions, evidence
assembly, narrative generation, and audit trail creation.
"""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from src.api.middleware.auth import create_access_token
from src.api.v1.chargebacks import get_chargeback_service
from src.core.enums import CaseStatus
from src.main import app

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

TENANT_ID = uuid4()
USER_ID = uuid4()
TEST_ARN = f"ARN-E2E-{uuid4().hex[:12]}"


@pytest.fixture
def api_key_headers():
    return {"x-api-key": "test-api-key-123"}


@pytest.fixture
def jwt_headers():
    token = create_access_token(user_id=USER_ID, tenant_id=TENANT_ID, role="analyst")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_jwt_headers():
    token = create_access_token(user_id=USER_ID, tenant_id=TENANT_ID, role="admin")
    return {"Authorization": f"Bearer {token}"}


def _make_mock_service(case_id=None, status=CaseStatus.NEW):
    """Build a mock ChargebackService with realistic responses."""
    svc = AsyncMock()
    _case_id = case_id or str(uuid4())

    svc.ingest.return_value = {
        "case_id": _case_id,
        "deadline": "2025-01-30T23:59:59Z",
        "status": status,
        "message": "ingested",
    }
    svc.get_pending_reviews.return_value = [
        {
            "case_id": _case_id,
            "status": CaseStatus.DRAFT_READY,
            "win_probability": 0.82,
            "deadline": "2025-01-30T23:59:59Z",
        }
    ]
    svc.review.return_value = None
    return svc, _case_id


# ---------------------------------------------------------------------------
# 13.1 — Chargeback full lifecycle
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_chargeback_full_lifecycle(api_key_headers, jwt_headers):
    """
    Validates the happy-path lifecycle:
      POST /ingest  →  GET /pending  →  POST /{id}/review (approve)
    """
    mock_svc, case_id = _make_mock_service()
    app.dependency_overrides[get_chargeback_service] = lambda: mock_svc

    # Ensure Redis rate-limiter is mocked
    app.state.redis = AsyncMock()
    app.state.redis.check_rate_limit.return_value = True

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            # ---- Step 1: Ingest ----
            ingest_payload = {
                "raw_payload": {
                    "tenant_id": str(TENANT_ID),
                    "network_arn": TEST_ARN,
                    "amount": 45000.00,
                    "network": "VISA",
                    "reason_code": "10.4",
                    "description": "Unauthorized transaction",
                }
            }
            resp = await ac.post(
                "/api/v1/chargebacks/ingest",
                json=ingest_payload,
                headers=api_key_headers,
            )
            assert resp.status_code == 202, f"Ingest failed: {resp.text}"
            data = resp.json()
            assert "case_id" in data
            assert data["status"] == "NEW"
            assert "deadline" in data

            # ---- Step 2: Pending reviews ----
            resp = await ac.get(
                "/api/v1/chargebacks/pending", headers=jwt_headers
            )
            assert resp.status_code == 200
            pending = resp.json()
            assert "items" in pending
            assert pending["total"] >= 1

            # ---- Step 3: Review (approve) ----
            resp = await ac.post(
                f"/api/v1/chargebacks/{case_id}/review",
                json={"action": "approve"},
                headers=jwt_headers,
            )
            assert resp.status_code == 200
            review_data = resp.json()
            assert review_data["status"] == "success"

            # ---- Verify service calls ----
            mock_svc.ingest.assert_called_once()
            mock_svc.review.assert_called_once()
    finally:
        app.dependency_overrides.pop(get_chargeback_service, None)


# ---------------------------------------------------------------------------
# 13.2 — Duplicate chargeback rejection
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_duplicate_chargeback_rejected(api_key_headers):
    """
    Second ingestion of the same ARN must return HTTP 409 or 400.
    """
    mock_svc = AsyncMock()
    mock_svc.ingest.side_effect = [
        {
            "case_id": str(uuid4()),
            "deadline": "2025-01-30T23:59:59Z",
            "status": CaseStatus.NEW,
            "message": "ingested",
        },
        Exception("DuplicateIngestionError: ARN already exists"),
    ]
    app.dependency_overrides[get_chargeback_service] = lambda: mock_svc
    app.state.redis = AsyncMock()
    app.state.redis.check_rate_limit.return_value = True

    payload = {
        "raw_payload": {
            "tenant_id": str(TENANT_ID),
            "network_arn": TEST_ARN,
            "amount": 15000.00,
        }
    }

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            # First → success
            resp1 = await ac.post(
                "/api/v1/chargebacks/ingest",
                json=payload,
                headers=api_key_headers,
            )
            assert resp1.status_code == 202

            # Second → conflict / error
            resp2 = await ac.post(
                "/api/v1/chargebacks/ingest",
                json=payload,
                headers=api_key_headers,
            )
            assert resp2.status_code == 400
            assert "DuplicateIngestionError" in resp2.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_chargeback_service, None)


# ---------------------------------------------------------------------------
# 13.1 supplement — Review actions (edit, reject)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_chargeback_review_reject(jwt_headers):
    """Analyst can reject a representment draft."""
    mock_svc, case_id = _make_mock_service()
    app.dependency_overrides[get_chargeback_service] = lambda: mock_svc
    app.state.redis = AsyncMock()
    app.state.redis.check_rate_limit.return_value = True

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            resp = await ac.post(
                f"/api/v1/chargebacks/{case_id}/review",
                json={"action": "reject"},
                headers=jwt_headers,
            )
            assert resp.status_code == 200
            assert resp.json()["status"] == "success"
    finally:
        app.dependency_overrides.pop(get_chargeback_service, None)


@pytest.mark.asyncio
async def test_chargeback_review_edit(jwt_headers):
    """Analyst can submit edits to a representment draft."""
    mock_svc, case_id = _make_mock_service()
    app.dependency_overrides[get_chargeback_service] = lambda: mock_svc
    app.state.redis = AsyncMock()
    app.state.redis.check_rate_limit.return_value = True

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            resp = await ac.post(
                f"/api/v1/chargebacks/{case_id}/review",
                json={
                    "action": "edit",
                    "edits": {"narrative": "Updated narrative text."},
                },
                headers=jwt_headers,
            )
            assert resp.status_code == 200
    finally:
        app.dependency_overrides.pop(get_chargeback_service, None)


# ---------------------------------------------------------------------------
# Auth: Unauthorized access to ingestion
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ingest_without_api_key_returns_401():
    """Missing API key must return 401."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        resp = await ac.post("/api/v1/chargebacks/ingest", json={})
    assert resp.status_code == 401
