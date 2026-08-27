import uuid

import pytest

from src.config import settings
from src.integrations.redis_client import RedisClient


@pytest.mark.asyncio
async def test_redis_client():
    client = RedisClient(settings.REDIS_URL)
    is_healthy = await client.health_check()
    assert is_healthy, "Redis health check failed"

    tenant_id = uuid.uuid4()
    cust_id = "test_cust"

    await client.set_feature_vector(cust_id, tenant_id, {"fraud_score": 0.95})
    data = await client.get_feature_vector(cust_id, tenant_id)
    assert data == {"fraud_score": 0.95}

    allowed, remaining = await client.check_rate_limit("test_limit", 5, 60)
    assert allowed

    await client.close()
