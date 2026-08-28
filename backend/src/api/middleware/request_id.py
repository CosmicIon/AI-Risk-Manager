"""Middleware for generating and propagating Request IDs."""

import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds an X-Request-ID header to every request if not present.
    It also adds the same header to the response.
    """

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = str(uuid.uuid4())

        # Add to request state for downstream access
        request.state.request_id = request_id

        # Propagate to tracing contexts (OpenTelemetry/Langfuse) if integrated here
        # For MVP, we just attach to the request state and response headers

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
