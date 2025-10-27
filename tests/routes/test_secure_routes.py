"""
Tests for secure routes requiring JWT authentication.
Phase 1: Test with new JWT structure (org_id, is_owner).
"""

import pytest
from httpx import ASGITransport, AsyncClient

from org_service.config import settings
from org_service.main import app
from org_service.utils.jwt import create_jwt_token


def get_valid_user_payload(overrides: dict | None = None) -> dict:
    """
    Return a valid Phase 1 user payload for testing JWT generation.
    """
    if overrides is None:
        overrides = {}
    return {
        "sub": "google-user-123",  # Google user ID
        "email": "test@example.com",
        "org_id": settings.hardcoded_org_id,
        "is_owner": True,
        **overrides,
    }


@pytest.mark.asyncio
async def test_whoami_returns_user_info():
    """Test that /secure/whoami returns user info from JWT."""
    payload = get_valid_user_payload()
    token = create_jwt_token(payload)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        resp = await ac.get("/secure/whoami", headers={"Authorization": f"Bearer {token}"})

    assert resp.status_code == 200
    data = resp.json()
    assert data["user"]["google_sub"] == payload["sub"]
    assert data["user"]["email"] == payload["email"]
    assert data["user"]["org_id"] == settings.hardcoded_org_id
    assert data["user"]["is_owner"] is True


@pytest.mark.asyncio
async def test_whoami_with_valid_token_returns_user():
    """Test that whoami with valid JWT returns 200."""
    payload = get_valid_user_payload()
    token = create_jwt_token(payload)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        resp = await ac.get("/secure/whoami", headers={"Authorization": f"Bearer {token}"})

    assert resp.status_code == 200
    assert resp.json()["user"]["email"] == payload["email"]


@pytest.mark.asyncio
async def test_whoami_without_token_returns_401():
    """Test that whoami without JWT returns 401."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        resp = await ac.get("/secure/whoami")

    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_whoami_with_malformed_token_returns_401():
    """Test that whoami with malformed JWT returns 401."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        resp = await ac.get("/secure/whoami", headers={"Authorization": "Bearer malformed.token"})

    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_whoami_with_expired_token_returns_401():
    """Test that whoami with expired JWT returns 401."""
    payload = get_valid_user_payload()
    token = create_jwt_token(payload, expiry_seconds=-1)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        resp = await ac.get("/secure/whoami", headers={"Authorization": f"Bearer {token}"})

    assert resp.status_code == 401
