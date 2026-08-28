"""
End-to-end test: Evaluation pipeline flow.

Tests the metrics / evaluation API endpoints: fetching evaluation
reports, Prometheus metrics scraping, cost-summary retrieval,
and role-based access control.
"""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from src.api.middleware.auth import create_access_token
from src.main import app

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

TENANT_ID = uuid4()
USER_ID = uuid4()


@pytest.fixture
def admin_headers():
    token = create_access_token(user_id=USER_ID, tenant_id=TENANT_ID, role="admin")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def data_scientist_headers():
    token = create_access_token(user_id=USER_ID, tenant_id=TENANT_ID, role="data_scientist")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def analyst_headers():
    token = create_access_token(user_id=USER_ID, tenant_id=TENANT_ID, role="analyst")
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# 13.6 — Prometheus metrics endpoint (public)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_prometheus_metrics_endpoint():
    """
    GET /v1/metrics/prometheus returns text/plain with Prometheus exposition format.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        resp = await ac.get("/api/v1/metrics/prometheus")

    assert resp.status_code == 200
    # Content-type should be text/plain or openmetrics
    assert "text/plain" in resp.headers.get("content-type", "")
    body = resp.text
    # Should contain at least the default python_info metric
    assert "python_info" in body or "process_" in body or "HELP" in body


# ---------------------------------------------------------------------------
# 13.6 — Evaluation report retrieval
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_evaluation_report_return_risk(admin_headers):
    """
    GET /v1/metrics/evaluation/return_risk/latest returns the latest evaluation.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        resp = await ac.get(
            "/api/v1/metrics/evaluation/return_risk/latest",
            headers=admin_headers,
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["model_name"] == "return_risk"
    assert 0 < data["f1_score"] <= 1.0
    assert 0 < data["roc_auc"] <= 1.0
    assert data["cost_weighted_loss"] >= 0
    assert "evaluated_at" in data


@pytest.mark.asyncio
async def test_get_evaluation_report_data_scientist(data_scientist_headers):
    """Data scientists can also access evaluation reports."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        resp = await ac.get(
            "/api/v1/metrics/evaluation/return_risk/latest",
            headers=data_scientist_headers,
        )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_get_evaluation_report_unknown_model(admin_headers):
    """Unknown model name returns 404."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        resp = await ac.get(
            "/api/v1/metrics/evaluation/nonexistent_model/latest",
            headers=admin_headers,
        )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_evaluation_report_analyst_forbidden(analyst_headers):
    """
    Analysts should not have access to evaluation reports (admin / data_scientist only).
    """
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        resp = await ac.get(
            "/api/v1/metrics/evaluation/return_risk/latest",
            headers=analyst_headers,
        )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# 13.6 — Cost summary
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cost_summary(admin_headers):
    """Admin can retrieve ₹-denominated cost summary."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        resp = await ac.get(
            "/api/v1/metrics/cost-summary",
            headers=admin_headers,
        )

    assert resp.status_code == 200
    data = resp.json()
    assert "total_fp_cost" in data
    assert "total_fn_cost" in data
    assert "total_savings" in data
    assert data["currency"] == "INR"


# ---------------------------------------------------------------------------
# 13.7 — Cross-cutting: health and readiness probes
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_health_probe():
    """GET /v1/health returns 200 with status ok."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        resp = await ac.get("/api/v1/health")

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "environment" in data
    assert "version" in data


@pytest.mark.asyncio
async def test_readiness_probe():
    """GET /v1/readiness returns 200 with dependency checks."""
    # Mock all state dependencies so they return True for health_check
    app.state.redis = AsyncMock()
    app.state.redis.health_check.return_value = True
    app.state.kafka = AsyncMock()
    app.state.kafka.health_check.return_value = True
    app.state.qdrant = AsyncMock()
    app.state.qdrant.health_check.return_value = True
    app.state.minio = AsyncMock()
    app.state.minio.health_check.return_value = True

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        resp = await ac.get("/api/v1/readiness")

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["checks"]["redis"] == "ok"
    assert data["checks"]["kafka"] == "ok"


@pytest.mark.asyncio
async def test_readiness_degraded():
    """When Redis is down, readiness returns 'degraded'."""
    app.state.redis = AsyncMock()
    app.state.redis.health_check.return_value = False
    app.state.kafka = AsyncMock()
    app.state.kafka.health_check.return_value = True
    app.state.qdrant = AsyncMock()
    app.state.qdrant.health_check.return_value = True
    app.state.minio = AsyncMock()
    app.state.minio.health_check.return_value = True

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        resp = await ac.get("/api/v1/readiness")

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "degraded"
    assert data["checks"]["redis"] == "failed"
