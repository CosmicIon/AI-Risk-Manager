import asyncio
import uuid

import pytest

from src.config import settings
from src.integrations.qdrant_client import QdrantVectorStore


@pytest.mark.asyncio
async def test_qdrant_client():
    client = QdrantVectorStore(settings.QDRANT_URL)
    is_healthy = await client.health_check()
    assert is_healthy, "Qdrant health check failed"

    await client.ensure_collection()

    case_id = str(uuid.uuid4())
    embedding = [0.1] * 1536
    payload = {
        "reason_code": "10.4",
        "network": "VISA",
        "amount_bucket": "high",
        "outcome": "WON",
        "narrative_summary": "Test narrative",
    }

    await client.upsert_case(case_id, embedding, payload)

    # Wait for indexing
    await asyncio.sleep(1)

    results = await client.search_similar(embedding, reason_code="10.4", network="VISA")
    assert len(results) >= 1
    assert any(r["case_id"] == case_id for r in results)

    await client.close()
