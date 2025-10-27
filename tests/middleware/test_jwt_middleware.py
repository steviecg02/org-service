"""
Tests for JWT middleware.
Phase 1: Test with new JWT structure (org_id, is_owner).
"""

import pytest


@pytest.mark.asyncio
async def test_jwt_middleware_accepts_valid_token(async_client, valid_jwt_token):
    """Test that middleware accepts valid JWT and allows access to protected route."""
    headers = {"Authorization": f"Bearer {valid_jwt_token}"}
    response = await async_client.get("/secure/whoami", headers=headers)
    assert response.status_code == 200
    assert response.json()["user"]["email"] == "test@example.com"
    assert response.json()["user"]["is_owner"] is True


@pytest.mark.asyncio
async def test_jwt_middleware_rejects_invalid_token(async_client):
    """Test that middleware rejects invalid JWT tokens."""
    headers = {"Authorization": "Bearer invalid.token.here"}
    response = await async_client.get("/secure/whoami", headers=headers)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_jwt_middleware_requires_token(async_client):
    """Test that middleware rejects requests without Authorization header."""
    response = await async_client.get("/secure/whoami")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_jwt_middleware_allows_exempt_paths(async_client):
    """Test that middleware allows access to exempt paths without JWT."""
    response = await async_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "uptime_seconds" in data
    assert "version" in data
    assert "checks" in data
