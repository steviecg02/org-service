"""
Test fixtures for org-service.
Phase 1: No database, minimal fixtures for OAuth + JWT testing.
"""

import time
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from jose import jwt

from org_service.config import settings
from org_service.main import app


# -- HTTPX client for test requests
@pytest_asyncio.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


# -- Mock Google OAuth service
@pytest.fixture
def mock_oauth(mocker):
    """Mock the Google OAuth client for testing auth routes."""
    mock = mocker.patch("org_service.services.auth_service.oauth")
    mock.google.authorize_access_token = AsyncMock()
    mock.google.parse_id_token = AsyncMock()
    return mock


# -- Valid JWT token fixture (Phase 1 structure)
@pytest.fixture
def valid_jwt_token():
    """Create a valid JWT token with Phase 1 structure (org_id, is_owner)."""
    now = int(time.time())
    payload = {
        "sub": "google-user-id-12345",  # Google user ID
        "org_id": settings.hardcoded_org_id,
        "email": "test@example.com",
        "is_owner": True,
        "exp": now + 3600,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
