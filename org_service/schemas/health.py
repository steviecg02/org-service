"""
Health check Pydantic schemas.
"""

from enum import Enum

from pydantic import BaseModel, Field


class HealthStatus(str, Enum):
    """Health status enum."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ComponentHealth(BaseModel):
    """Individual component health check."""

    status: HealthStatus = Field(..., description="Component health status")
    message: str | None = Field(None, description="Optional status message")
    response_time_ms: float | None = Field(None, description="Response time in milliseconds")

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "healthy",
                "message": "API responding normally",
                "response_time_ms": 1.23,
            }
        }
    }


class HealthResponse(BaseModel):
    """
    Comprehensive health check response.

    Phase 1: Simple status indicator with uptime.
    Future phases will add database and external service checks.
    """

    status: HealthStatus = Field(..., description="Overall service health status")
    version: str = Field(default="1.0.0", description="Service version")
    uptime_seconds: float = Field(..., description="Service uptime in seconds")
    checks: dict[str, ComponentHealth] = Field(
        default_factory=dict, description="Individual component health checks"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "uptime_seconds": 3600.5,
                "checks": {
                    "api": {
                        "status": "healthy",
                        "message": "API responding",
                        "response_time_ms": 0.5,
                    }
                },
            }
        }
    }


class LivenessResponse(BaseModel):
    """
    Liveness probe response for Kubernetes.

    Returns simple status to indicate if the service is alive.
    """

    status: str = Field(default="alive", description="Liveness status")

    model_config = {"json_schema_extra": {"example": {"status": "alive"}}}


class ReadinessResponse(BaseModel):
    """
    Readiness probe response for Kubernetes.

    Returns status indicating if service is ready to accept traffic.
    """

    status: str = Field(..., description="Readiness status")
    ready: bool = Field(..., description="Whether service is ready")

    model_config = {"json_schema_extra": {"example": {"status": "ready", "ready": True}}}
