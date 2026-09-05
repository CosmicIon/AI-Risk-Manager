"""
Unit tests for Real-Time Fraud Scoring Microservice (Module 4.1 - FastAPI).
Validates health checks, single/batch inference, sub-50ms latency, 3-tier triage, and metrics.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from fastapi.testclient import TestClient

from src.api import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_health_check_endpoint(client):
    """Ensure /health endpoint returns operational status and model readiness."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["model_loaded"] is True
    assert data["features_count"] > 0
    assert data["version"] == "v2.1"
    assert data["uptime_seconds"] >= 0.0


def test_root_info_endpoint(client):
    """Ensure root endpoint returns service metadata and endpoints."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "docs_url" in data
    assert "health_url" in data
    assert "metrics_url" in data


def test_evaluate_single_transaction_contract_and_latency(client):
    """Verify single transaction evaluation schema, decision values, and <50ms latency."""
    payload = {
        "transaction_id": 9001,
        "customer_id": 5,
        "terminal_id": 12,
        "tx_amount": 35.50,
        "tx_datetime": "2026-09-04T14:30:00",
    }
    response = client.post("/v1/risk/evaluate", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["transaction_id"] == 9001
    assert 0.0 <= data["risk_score"] <= 1.0
    assert data["decision"] in ["APPROVE", "CHALLENGE", "DECLINE"]
    assert isinstance(data["reasons"], list) and len(data["reasons"]) > 0
    assert "Z" in data["timestamp"]

    # Latency requirement: sub-50ms (in test client, usually < 15ms)
    assert data["latency_ms"] < 50.0, f"Latency {data['latency_ms']}ms exceeded 50ms SLA"


def test_evaluate_high_risk_transaction_reason_codes(client):
    """Verify that extreme transaction anomalies trigger elevated risk and informative reason codes."""
    payload = {
        "transaction_id": 9002,
        "customer_id": 1,
        "terminal_id": 99,
        "tx_amount": 4800.0,  # Extreme anomaly
        "tx_datetime": "2026-09-04T03:15:00",  # Night window
    }
    response = client.post("/v1/risk/evaluate", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["transaction_id"] == 9002
    assert data["decision"] in ["CHALLENGE", "DECLINE"]
    assert data["risk_score"] >= 0.30

    # Ensure reason codes highlight anomalies
    reasons_str = " ".join(data["reasons"]).lower()
    assert any(keyword in reasons_str for keyword in ["amount", "higher", "baseline", "night", "deviation", "risk"])


def test_evaluate_batch_transactions(client):
    """Verify micro-batch scoring correctly processes multiple transactions."""
    batch_payload = {
        "transactions": [
            {
                "transaction_id": 8001,
                "customer_id": 10,
                "terminal_id": 20,
                "tx_amount": 25.0,
                "tx_datetime": "2026-09-04T10:00:00",
            },
            {
                "transaction_id": 8002,
                "customer_id": 12,
                "terminal_id": 30,
                "tx_amount": 2500.0,
                "tx_datetime": "2026-09-04T02:00:00",
            },
        ]
    }
    response = client.post("/v1/risk/evaluate/batch", json=batch_payload)
    assert response.status_code == 200
    data = response.json()

    assert len(data) == 2
    assert data[0]["transaction_id"] == 8001
    assert data[1]["transaction_id"] == 8002


def test_metrics_telemetry_aggregation(client):
    """Verify telemetry correctly tracks requests, latency statistics, and decisions."""
    # Issue a transaction to ensure metrics are non-zero
    client.post(
        "/v1/risk/evaluate",
        json={"transaction_id": 7777, "customer_id": 2, "terminal_id": 3, "tx_amount": 45.0},
    )

    response = client.get("/metrics")
    assert response.status_code == 200
    metrics = response.json()

    assert metrics["total_requests"] >= 1
    assert metrics["avg_latency_ms"] >= 0.0
    assert metrics["p95_latency_ms"] >= 0.0
    assert sum(metrics["decisions"].values()) == metrics["total_requests"]


def test_invalid_transaction_payload_validation(client):
    """Verify Pydantic validation rejects negative amount or missing required fields with HTTP 422."""
    # Negative amount
    bad_payload = {
        "transaction_id": 9999,
        "customer_id": 1,
        "terminal_id": 1,
        "tx_amount": -50.0,
    }
    response = client.post("/v1/risk/evaluate", json=bad_payload)
    assert response.status_code == 422
