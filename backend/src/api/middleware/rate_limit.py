"""Rate limiting middleware and dependencies."""

from fastapi import HTTPException, Request, status

from src.integrations.redis_client import RedisClient


def rate_limit(limit: int, window_seconds: int):
    """
    Dependency generator for route-specific rate limiting.
    Requires the request to have a tenant_id or client IP to use as identifier.
    """
    async def limiter(request: Request):
        # We need a Redis client instance. Let's get it from the app state
        # assuming it will be attached during startup.
        redis_client: RedisClient = request.app.state.redis

        # Determine identifier: tenant_id from auth if available, else client IP
        identifier = "unknown"

        # We can extract tenant_id from request state if auth middleware puts it there
        # but for simplicity, we'll try to use the client IP
        if request.client:
            identifier = request.client.host

        # Optional: check if we have an API key or auth token to use as identifier
        api_key = request.headers.get("x-api-key")
        if api_key:
            identifier = f"apikey:{api_key}"

        allowed, _ = await redis_client.check_rate_limit(
            identifier=f"ratelimit:{request.url.path}:{identifier}",
            limit=limit,
            window=window_seconds
        )

        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too Many Requests",
                headers={"Retry-After": str(window_seconds)}
            )

    return limiter
