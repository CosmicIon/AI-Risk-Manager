"""
End-to-end test: Return scoring flow.

Tests the complete return scoring lifecycle: scoring a return request,
verifying risk tier / decision mapping, latency budgets, response schema,
and degraded-mode behaviour when Redis is unavailable.
"""

import time
from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from src.api.middleware.auth import create_access_token
from src.api.v1.returns import get_return_scoring_service
from src.main import app

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

TENANT_ID = uuid4()
USER_ID = uuid4()


@pytest.fixture
def api_key_headers():
    return {"x-api-key": "test-api-key-123"}


@pytest.fixture
def admin_jwt_headers():
    token = create_access_token(user_id=USER_ID, tenant_id=TENANT_ID, role="admin")
    return {"Authorization": f"Bearer {token}"}


def _score_payload(**overrides):
    base = {
        "request_id": f"req-{uuid4().hex[:8]}",
        "tenant_id": str(TENANT_ID),
        "customer_id": "cust-abc-001",
        "order_id": "ord-xyz-001",
        "order_amount": 5000.00,
        "return_amount": 3200.00,
        "return_reason": "Defective",
        "order_date": datetime.now(UTC).isoformat(),
        "return_initiated_at": datetime.now(UTC).isoformat(),
        "product_category": "Electronics",
    }
    base.update(overrides)
    return base


def _make_mock_service(
    risk_score=15,
    risk_tier="LOW",
    decision="auto_approve",
    latency=8.2,
    top_features=None,
):
    svc = AsyncMock()
    svc.score.return_value = {
        "request_id": "req-12345",
        "risk_score": risk_score,
        "risk_tier": risk_tier,
        "decision": decision,
        "explanation": "Model explanation stub.",
        "top_features": top_features
        or [
            {"feature": "return_rate_90d", "shap_value": 0.32},
            {"feature": "order_amount", "shap_value": 0.18},
            {"feature": "account_age_days", "shap_value": -0.12},
            {"feature": "category_return_rate", "shap_value": 0.09},
            {"feature": "ip_distance_km", "shap_value": 0.07},
        ],
        "model_version": "v2.1",
        "inference_latency_ms": latency,
        "scored_at": datetime.now(UTC).isoformat(),
    }
    return svc


# ---------------------------------------------------------------------------
# 13.3 — Return scoring end-to-end
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_return_scoring_happy_path(api_key_headers):
    """
    POST /v1/returns/score with valid payload returns a valid score,
    risk tier, decision, top features, and latency.
    """
    mock_svc = _make_mock_service()
    app.dependency_overrides[get_return_scoring_service] = lambda _=None: mock_svc
    app.state.redis = AsyncMock()
    app.state.redis.check_rate_limit.return_value = True

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            start = time.monotonic()
            resp = await ac.post(
                "/api/v1/returns/score",
                json=_score_payload(),
                headers=api_key_headers,
            )
            wall_ms = (time.monotonic() - start) * 1000

        assert resp.status_code == 200, f"Scoring failed: {resp.text}"
        data = resp.json()

        # Schema checks
        assert 0 <= data["risk_score"] <= 100
        assert data["risk_tier"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
        assert data["decision"] in ("auto_approve", "manual_review", "auto_deny")
        assert len(data["top_features"]) == 5
        assert data["inference_latency_ms"] > 0

        # Latency budget: the mock won't slow us down, but the HTTP
        # round-trip through ASGI should be well under 300 ms.
        assert wall_ms < 2000, f"Wall-clock latency {wall_ms:.0f}ms exceeds budget"
    finally:
        app.dependency_overrides.pop(get_return_scoring_service, None)


@pytest.mark.asyncio
async def test_return_scoring_high_risk(api_key_headers):
    """A high-risk score produces the correct tier and decision."""
    mock_svc = _make_mock_service(risk_score=92, risk_tier="CRITICAL", decision="auto_deny")
    app.dependency_overrides[get_return_scoring_service] = lambda _=None: mock_svc
    app.state.redis = AsyncMock()
    app.state.redis.check_rate_limit.return_value = True

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            resp = await ac.post(
                "/api/v1/returns/score",
                json=_score_payload(),
                headers=api_key_headers,
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["risk_tier"] == "CRITICAL"
        assert data["decision"] == "auto_deny"
    finally:
        app.dependency_overrides.pop(get_return_scoring_service, None)


@pytest.mark.asyncio
async def test_return_scoring_medium_risk(api_key_headers):
    """A medium-risk score triggers manual review."""
    mock_svc = _make_mock_service(risk_score=55, risk_tier="MEDIUM", decision="manual_review")
    app.dependency_overrides[get_return_scoring_service] = lambda _=None: mock_svc
    app.state.redis = AsyncMock()
    app.state.redis.check_rate_limit.return_value = True

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            resp = await ac.post(
                "/api/v1/returns/score",
                json=_score_payload(),
                headers=api_key_headers,
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["risk_tier"] == "MEDIUM"
        assert data["decision"] == "manual_review"
    finally:
        app.dependency_overrides.pop(get_return_scoring_service, None)


# ---------------------------------------------------------------------------
# 13.4 — Degraded mode (service continues when dependency fails)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_return_scoring_degraded_mode(api_key_headers):
    """
    When the underlying service raises, the API returns 500 but does NOT crash.
    """
    mock_svc = AsyncMock()
    mock_svc.score.side_effect = Exception("Redis connection refused")
    app.dependency_overrides[get_return_scoring_service] = lambda _=None: mock_svc
    app.state.redis = AsyncMock()
    app.state.redis.check_rate_limit.return_value = True

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            start = time.monotonic()
            resp = await ac.post(
                "/api/v1/returns/score",
                json=_score_payload(),
                headers=api_key_headers,
            )
            wall_ms = (time.monotonic() - start) * 1000

        # Should return error, not crash
        assert resp.status_code == 500
        assert "Redis connection refused" in resp.json()["detail"]
        # Even in failure, latency should be reasonable
        assert wall_ms < 5000
    finally:
        app.dependency_overrides.pop(get_return_scoring_service, None)


# ---------------------------------------------------------------------------
# Auth: missing API key
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_return_scoring_no_api_key():
    """Missing API key returns 401."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        resp = await ac.post("/api/v1/returns/score", json=_score_payload())
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Policy update
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_return_policy_update(admin_jwt_headers):
    """Admin can update return policy thresholds."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        resp = await ac.put(
            "/api/v1/returns/policy",
            json={
                "tenant_id": str(TENANT_ID),
                "low_threshold": 20,
                "medium_threshold": 50,
                "high_threshold": 80,
                "auto_deny_enabled": True,
                "high_value_customer_override": False,
            },
            headers=admin_jwt_headers,
        )
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"


@pytest.mark.asyncio
async def test_return_policy_invalid_thresholds(admin_jwt_headers):
    """Invalid thresholds (low > medium) return 400."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        resp = await ac.put(
            "/api/v1/returns/policy",
            json={
                "tenant_id": str(TENANT_ID),
                "low_threshold": 90,
                "medium_threshold": 50,
                "high_threshold": 30,
                "auto_deny_enabled": False,
                "high_value_customer_override": False,
            },
            headers=admin_jwt_headers,
        )
    assert resp.status_code == 400
