"""
Prometheus metrics middleware for monitoring HTTP requests.
"""

import time

from prometheus_client import Counter, Gauge, Histogram
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

# Define Prometheus metrics
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0),
)

REQUEST_IN_PROGRESS = Gauge(
    "http_requests_in_progress",
    "HTTP requests currently in progress",
    ["method", "endpoint"],
)

RESPONSE_SIZE = Histogram(
    "http_response_size_bytes",
    "HTTP response size in bytes",
    ["method", "endpoint"],
)


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Collect Prometheus metrics for all HTTP requests.

    Tracks:
    - Request count by method, endpoint, and status code
    - Request latency (duration)
    - Requests in progress
    - Response size
    """

    async def dispatch(self, request: Request, call_next):  # type: ignore[no-untyped-def]
        """
        Process request and collect metrics.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/route handler

        Returns:
            HTTP response
        """
        # Skip metrics endpoint itself to avoid recursion
        if request.url.path == "/metrics":
            return await call_next(request)

        # Get endpoint for metrics (use path template if available)
        endpoint = request.url.path
        method = request.method

        # Track request start
        start_time = time.time()
        REQUEST_IN_PROGRESS.labels(method=method, endpoint=endpoint).inc()

        try:
            # Process request
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time

            # Record metrics
            REQUEST_COUNT.labels(
                method=method, endpoint=endpoint, status_code=response.status_code
            ).inc()

            REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(duration)

            # Try to get response size
            if hasattr(response, "body"):
                response_size = len(response.body)
                RESPONSE_SIZE.labels(method=method, endpoint=endpoint).observe(response_size)

            return response

        finally:
            # Always decrement in-progress gauge
            REQUEST_IN_PROGRESS.labels(method=method, endpoint=endpoint).dec()
