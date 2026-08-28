"""
End-to-end test: Fraud detection flow.

Tests the fraud alerting API endpoints: listing alerts, registering
known calendar events (to suppress false positives), acknowledging
alerts, and verifying auth / role restrictions.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from src.api.middleware.auth import create_access_token
from src.api.v1.fraud import get_fraud_service
from src.main import app

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

TENANT_ID = uuid4()
USER_ID = uuid4()


@pytest.fixture
def analyst_headers():
    token = create_access_token(user_id=USER_ID, tenant_id=TENANT_ID, role="analyst")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers():
    token = create_access_token(user_id=USER_ID, tenant_id=TENANT_ID, role="admin")
    return {"Authorization": f"Bearer {token}"}


def _make_mock_fraud_service():
    svc = AsyncMock()
    svc.get_active_alerts.return_value = [
        {
            "alert_id": "alert-001",
            "severity": "critical",
            "anomaly_type": "velocity_spike",
            "description": "142 TPS vs 12 baseline",
            "created_at": datetime.now(UTC).isoformat(),
        },
        {
            "alert_id": "alert-002",
            "severity": "high",
            "anomaly_type": "geo_anomaly",
            "description": "Multiple countries in 10 min window",
            "created_at": datetime.now(UTC).isoformat(),
        },
        {
            "alert_id": "alert-003",
            "severity": "medium",
            "anomaly_type": "velocity_spike",
            "description": "35 TPS vs 10 baseline",
            "created_at": datetime.now(UTC).isoformat(),
        },
    ]
    svc.register_event.return_value = None
    return svc


# ---------------------------------------------------------------------------
# 13.5 — Fraud alerts listing
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_fraud_alerts(analyst_headers):
    """Analyst can list active fraud alerts."""
    mock_svc = _make_mock_fraud_service()
    app.dependency_overrides[get_fraud_service] = lambda: mock_svc

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            resp = await ac.get("/api/v1/fraud/alerts", headers=analyst_headers)

        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert data["total"] == 3
    finally:
        app.dependency_overrides.pop(get_fraud_service, None)


@pytest.mark.asyncio
async def test_get_fraud_alerts_filter_severity(analyst_headers):
    """Severity filter narrows the result set."""
    mock_svc = _make_mock_fraud_service()
    app.dependency_overrides[get_fraud_service] = lambda: mock_svc

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            resp = await ac.get(
                "/api/v1/fraud/alerts?severity=critical",
                headers=analyst_headers,
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["severity"] == "critical"
    finally:
        app.dependency_overrides.pop(get_fraud_service, None)


@pytest.mark.asyncio
async def test_get_fraud_alerts_filter_classification(analyst_headers):
    """Classification filter narrows the result set."""
    mock_svc = _make_mock_fraud_service()
    app.dependency_overrides[get_fraud_service] = lambda: mock_svc

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            resp = await ac.get(
                "/api/v1/fraud/alerts?classification=velocity_spike",
                headers=analyst_headers,
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        for item in data["items"]:
            assert item["anomaly_type"] == "velocity_spike"
    finally:
        app.dependency_overrides.pop(get_fraud_service, None)


# ---------------------------------------------------------------------------
# 13.5 — Register known event (false-positive suppression)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_register_known_event(admin_headers):
    """Admin can register a calendar event to suppress false positives."""
    mock_svc = _make_mock_fraud_service()
    app.dependency_overrides[get_fraud_service] = lambda: mock_svc

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            resp = await ac.post(
                "/api/v1/fraud/events",
                json={
                    "name": "Big Billion Days",
                    "start": datetime.now(UTC).isoformat(),
                    "end": (datetime.now(UTC) + timedelta(days=5)).isoformat(),
                    "threshold_multiplier": 3.0,
                },
                headers=admin_headers,
            )

        assert resp.status_code == 200
        assert "Big Billion Days" in resp.json()["message"]
        mock_svc.register_event.assert_called_once()
    finally:
        app.dependency_overrides.pop(get_fraud_service, None)


@pytest.mark.asyncio
async def test_register_event_requires_admin(analyst_headers):
    """Analyst (non-admin) cannot register events → 403."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        resp = await ac.post(
            "/api/v1/fraud/events",
            json={
                "name": "Test Event",
                "start": datetime.now(UTC).isoformat(),
                "end": (datetime.now(UTC) + timedelta(hours=2)).isoformat(),
            },
            headers=analyst_headers,
        )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# 13.5 — Alert acknowledgement
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_acknowledge_alert(analyst_headers):
    """Analyst can acknowledge an alert."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        resp = await ac.post(
            "/api/v1/fraud/alerts/alert-001/acknowledge",
            headers=analyst_headers,
        )
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"


# ---------------------------------------------------------------------------
# Auth: no JWT
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fraud_alerts_no_jwt():
    """Missing JWT returns 403."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        resp = await ac.get("/api/v1/fraud/alerts")
    assert resp.status_code == 401
