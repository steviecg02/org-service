"""
Tests for authentication routes.
Phase 1: Test Google OAuth login and callback (no database).
"""

import pytest
from fastapi import status
from httpx import ASGITransport, AsyncClient
from jose import jwt

from org_service.config import settings
from org_service.main import app


@pytest.mark.asyncio
async def test_login_redirects_to_google():
    """Test that /auth/login redirects to Google OAuth."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        resp = await ac.get("/auth/login", follow_redirects=False)
    assert resp.status_code == status.HTTP_302_FOUND
    assert "accounts.google.com" in resp.headers["location"]


@pytest.mark.asyncio
async def test_callback_with_invalid_state_returns_400(async_client):
    """Test that OAuth callback with invalid state returns 400."""
    response = await async_client.get("/auth/callback?state=bad&code=123")
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_callback_returns_jwt_with_hardcoded_org_id(async_client, mock_oauth):
    """
    Test that successful OAuth callback returns JWT with hardcoded org_id.
    Phase 1: No database - just return JWT with Google user info + hardcoded values.
    """
    # Mock Google OAuth responses
    mock_oauth.google.authorize_access_token.return_value = {"access_token": "fake-access-token"}
    mock_oauth.google.parse_id_token.return_value = {
        "sub": "google-user-123",
        "email": "testuser@example.com",
        "name": "Test User",
    }

    # Call the callback endpoint
    response = await async_client.get("/auth/callback?code=fakecode&state=fakestate")
    assert response.status_code == 200

    # Verify response contains JWT
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    # Decode JWT and verify it contains expected fields
    decoded = jwt.decode(
        data["access_token"],
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )

    assert decoded["sub"] == "google-user-123"
    assert decoded["email"] == "testuser@example.com"
    assert decoded["org_id"] == settings.hardcoded_org_id
    assert decoded["is_owner"] is True


@pytest.mark.asyncio
async def test_callback_with_missing_email_returns_400(async_client, mock_oauth):
    """Test that OAuth callback with incomplete user info returns 400."""
    mock_oauth.google.authorize_access_token.return_value = {"access_token": "fake-access-token"}
    # Missing email
    mock_oauth.google.parse_id_token.return_value = {
        "sub": "google-user-123",
        "name": "Test User",
    }

    response = await async_client.get("/auth/callback?code=fakecode&state=fakestate")
    assert response.status_code == 400
