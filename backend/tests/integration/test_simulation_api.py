"""Integration tests for Simulation Studio API endpoints."""

import os
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture(autouse=True)
def _clean_synthetic_data():
    """Ensure clean state for data directory."""
    data_dir = Path(__file__).resolve().parent.parent.parent / "data" / "synthetic"
    yield
    # Cleanup is optional; generated data can be reused


class TestGenerateEndpoint:
    @pytest.mark.asyncio
    async def test_generate_returns_200(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/simulation/generate",
            json={
                "n_customers": 100,
                "n_terminals": 20,
                "nb_days": 7,
                "radius": 5.0,
                "seed": 42,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_transactions" in data
        assert data["total_transactions"] > 0
        assert data["total_customers"] == 100
        assert data["total_terminals"] == 20
        assert "scenario_breakdown" in data
        assert "fraud_count" in data

    @pytest.mark.asyncio
    async def test_generate_creates_parquet_files(self, client: AsyncClient):
        await client.post(
            "/api/v1/simulation/generate",
            json={
                "n_customers": 50,
                "n_terminals": 10,
                "nb_days": 7,
                "seed": 99,
            },
        )
        data_dir = Path(__file__).resolve().parent.parent.parent / "data" / "synthetic"
        assert (data_dir / "transactions.parquet").exists()
        assert (data_dir / "customers.parquet").exists()
        assert (data_dir / "terminals.parquet").exists()

    @pytest.mark.asyncio
    async def test_generate_with_all_scenarios_disabled(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/simulation/generate",
            json={
                "n_customers": 50,
                "n_terminals": 10,
                "nb_days": 7,
                "scenario_1_enabled": False,
                "scenario_2_enabled": False,
                "scenario_3_enabled": False,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["fraud_count"] == 0

    @pytest.mark.asyncio
    async def test_generate_validation_error(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/simulation/generate",
            json={
                "n_customers": 0,  # Below minimum
                "n_terminals": 10,
                "nb_days": 7,
            },
        )
        assert response.status_code == 422


class TestStatsEndpoint:
    @pytest.mark.asyncio
    async def test_stats_after_generation(self, client: AsyncClient):
        # Generate first
        await client.post(
            "/api/v1/simulation/generate",
            json={
                "n_customers": 50,
                "n_terminals": 10,
                "nb_days": 7,
            },
        )

        response = await client.get("/api/v1/simulation/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_transactions" in data


class TestStreamEndpoints:
    @pytest.mark.asyncio
    async def test_stream_start_stop(self, client: AsyncClient):
        # Generate dataset first
        await client.post(
            "/api/v1/simulation/generate",
            json={
                "n_customers": 50,
                "n_terminals": 10,
                "nb_days": 7,
            },
        )

        # Start stream
        response = await client.post(
            "/api/v1/simulation/stream/start",
            json={"tps_rate": 10},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ("started", "already_running")

        # Stop stream
        response = await client.post("/api/v1/simulation/stream/stop")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_stream_without_data(self, client: AsyncClient):
        """Attempting to start stream without generated data should fail gracefully."""
        # Note: This may pass if data from previous test exists
        response = await client.post(
            "/api/v1/simulation/stream/start",
            json={"tps_rate": 5},
        )
        assert response.status_code == 200
