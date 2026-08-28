import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from src.integrations.prometheus_metrics import requests_total

class PrometheusMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # We process the request first
        response = await call_next(request)
        
        # After response, record the metrics
        method = request.method
        # Use route path if available to avoid high cardinality, else raw path
        route = request.scope.get("route")
        endpoint = route.path if route else request.url.path
        
        status_code = response.status_code
        
        # Ignore Prometheus scrape endpoint itself to avoid noise
        if endpoint != "/api/v1/metrics/prometheus":
            requests_total.labels(method=method, endpoint=endpoint, status_code=status_code).inc()
            
        return response
