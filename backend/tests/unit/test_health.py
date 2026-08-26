"""Unit tests for health and readiness endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check_returns_200(async_client: AsyncClient):
    """Verify /health returns 200 and valid JSON schema."""
    response = await async_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert data["environment"] == "dev"


@pytest.mark.asyncio
async def test_api_v1_health_check_returns_200(async_client: AsyncClient):
    """Verify /api/v1/health also routes correctly."""
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_readiness_check_returns_200(async_client: AsyncClient):
    """Verify /readiness returns component status."""
    response = await async_client.get("/readiness")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "checks" in data
    assert isinstance(data["checks"], dict)
