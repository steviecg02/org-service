"""
org-service FastAPI application.
Phase 1: Minimal Google OAuth + JWT authentication (no database).
"""

import time

from fastapi import FastAPI, Response, status
from prometheus_client import generate_latest
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware

from org_service.config import settings
from org_service.middleware.jwt_middleware import JWTMiddleware
from org_service.middleware.metrics_middleware import MetricsMiddleware
from org_service.middleware.request_id_middleware import RequestIDMiddleware
from org_service.routes import auth_routes, secure_routes
from org_service.schemas.health import (
    ComponentHealth,
    HealthResponse,
    HealthStatus,
    LivenessResponse,
    ReadinessResponse,
)

# Track service startup time
STARTUP_TIME = time.time()

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

middleware = [
    Middleware(MetricsMiddleware),  # First: Collect metrics for all requests
    Middleware(RequestIDMiddleware),  # Second: Add request ID to all requests
    Middleware(SessionMiddleware, secret_key=settings.jwt_secret_key),
    Middleware(
        JWTMiddleware,
        exempt_paths=[
            "/auth/login",
            "/auth/callback",
            "/docs",
            "/openapi.json",
            "/redoc",
            "/health",
            "/live",
            "/ready",
            "/metrics",
            "/favicon.ico",
        ],
    ),
]

app = FastAPI(
    title="Org Service API",
    description="""
    **Organization Service** - Google OAuth 2.0 + JWT Authentication

    ## Features

    * **Google OAuth Authentication** - Secure login via Google
    * **JWT Token Management** - Issue and validate JWT access tokens
    * **Rate Limiting** - Protect endpoints from abuse (10 requests/minute)
    * **Request Tracing** - X-Request-ID header for distributed tracing
    * **Structured Logging** - JSON-formatted logs for easy parsing

    ## Phase 1: No Database

    This is a minimal implementation without a database. All users get:
    - Hardcoded org_id: `11111111-1111-1111-1111-111111111111`
    - Owner privileges: `is_owner: true`

    ## Authentication Flow

    1. Visit `/auth/login` to initiate Google OAuth
    2. User authorizes via Google consent screen
    3. Callback returns JWT access token
    4. Use token in `Authorization: Bearer <token>` header for protected endpoints

    ## Example Usage

    ```bash
    # Get user info (requires authentication)
    curl -H "Authorization: Bearer <your-jwt-token>" https://api.example.com/secure/whoami
    ```
    """,
    version="1.0.0",
    middleware=middleware,
    contact={
        "name": "API Support",
        "email": "support@example.com",
    },
    license_info={
        "name": "MIT",
    },
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(auth_routes.router)
app.include_router(secure_routes.router)


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Comprehensive health check",
    description="Returns detailed health status with component checks. Use for monitoring dashboards.",
    responses={
        200: {"description": "Service is healthy"},
        503: {"description": "Service is unhealthy"},
    },
)
async def health_check() -> Response:
    """
    Comprehensive health check with component status.

    Returns detailed health information including:
    - Overall service status
    - Uptime
    - Individual component health

    Returns:
        HealthResponse: Detailed health status (200 if healthy, 503 if unhealthy)
    """
    checks: dict[str, ComponentHealth] = {}

    # Check 1: API is responding
    start_time = time.time()
    checks["api"] = ComponentHealth(
        status=HealthStatus.HEALTHY,
        message="API responding",
        response_time_ms=(time.time() - start_time) * 1000,
    )

    # Future: Add database check, external service checks, etc.

    # Determine overall status
    statuses = [check.status for check in checks.values()]
    if any(s == HealthStatus.UNHEALTHY for s in statuses):
        overall_status = HealthStatus.UNHEALTHY
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    elif any(s == HealthStatus.DEGRADED for s in statuses):
        overall_status = HealthStatus.DEGRADED
        status_code = status.HTTP_200_OK
    else:
        overall_status = HealthStatus.HEALTHY
        status_code = status.HTTP_200_OK

    health_response = HealthResponse(
        status=overall_status,
        version="1.0.0",
        uptime_seconds=time.time() - STARTUP_TIME,
        checks=checks,
    )

    return Response(
        content=health_response.model_dump_json(),
        status_code=status_code,
        media_type="application/json",
    )


@app.get(
    "/live",
    response_model=LivenessResponse,
    tags=["Health"],
    summary="Kubernetes liveness probe",
    description="Simple liveness check. Returns 200 if service is alive. Use for Kubernetes liveness probe.",
)
async def liveness() -> LivenessResponse:
    """
    Liveness probe for Kubernetes.

    Returns a simple status indicating the service is alive.
    This endpoint should return 200 as long as the process is running.

    Kubernetes will restart the pod if this endpoint fails.

    Returns:
        LivenessResponse: Liveness status
    """
    return LivenessResponse(status="alive")


@app.get(
    "/ready",
    response_model=ReadinessResponse,
    tags=["Health"],
    summary="Kubernetes readiness probe",
    description="Readiness check indicating if service can accept traffic. Use for Kubernetes readiness probe.",
    responses={
        200: {"description": "Service is ready"},
        503: {"description": "Service is not ready"},
    },
)
async def readiness() -> Response:
    """
    Readiness probe for Kubernetes.

    Returns status indicating if the service is ready to accept traffic.
    This should check if all dependencies are available.

    Kubernetes will not send traffic to the pod if this endpoint fails.

    Returns:
        ReadinessResponse: Readiness status (200 if ready, 503 if not ready)
    """
    # Phase 1: Always ready since we have no external dependencies
    # Future: Check database connection, external services, etc.
    ready = True

    if ready:
        return Response(
            content=ReadinessResponse(status="ready", ready=True).model_dump_json(),
            status_code=status.HTTP_200_OK,
            media_type="application/json",
        )
    return Response(
        content=ReadinessResponse(status="not_ready", ready=False).model_dump_json(),
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        media_type="application/json",
    )


@app.get(
    "/metrics",
    tags=["Monitoring"],
    summary="Prometheus metrics endpoint",
    description="Exposes Prometheus metrics for monitoring. Does not require authentication.",
    include_in_schema=False,  # Hide from Swagger docs
)
async def metrics() -> Response:
    """
    Prometheus metrics endpoint.

    Returns metrics in Prometheus text format for scraping.

    Returns:
        Response: Prometheus metrics
    """
    return Response(content=generate_latest(), media_type="text/plain")
