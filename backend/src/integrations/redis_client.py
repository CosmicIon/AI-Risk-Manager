import json
import logging
from typing import Any
import redis.asyncio as redis
from uuid import UUID

logger = logging.getLogger(__name__)

class RedisClient:
    def __init__(self, redis_url: str):
        self.pool = redis.ConnectionPool.from_url(
            redis_url,
            max_connections=50,
            decode_responses=True,
            socket_timeout=2.0,
            retry_on_timeout=True
        )
        self.client = redis.Redis(connection_pool=self.pool)

    async def get_feature_vector(self, customer_id: str, tenant_id: UUID) -> dict[str, float] | None:
        key = f"features:{tenant_id}:{customer_id}"
        data = await self.client.get(key)
        if data:
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                logger.error(f"Failed to decode feature vector for {key}")
                return None
        return None

    async def set_feature_vector(self, customer_id: str, tenant_id: UUID, features: dict[str, float], ttl: int = 3600):
        key = f"features:{tenant_id}:{customer_id}"
        await self.client.set(key, json.dumps(features), ex=ttl)

    async def increment_counter(self, key: str, window_seconds: int) -> int:
        """Increment a counter and set expiration if it's new."""
        pipe = self.client.pipeline()
        pipe.incr(key)
        pipe.expire(key, window_seconds, nx=True)
        results = await pipe.execute()
        return results[0]

    async def check_rate_limit(self, identifier: str, limit: int, window: int) -> tuple[bool, int]:
        """
        Token bucket / fixed window rate limiting.
        Returns (is_allowed, remaining)
        """
        key = f"ratelimit:{identifier}"
        current = await self.increment_counter(key, window)
        remaining = max(0, limit - current)
        return (current <= limit, remaining)

    async def health_check(self) -> bool:
        try:
            return await self.client.ping()
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False

    async def close(self):
        await self.client.aclose()
