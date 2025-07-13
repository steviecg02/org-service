import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from fastapi import status
from sqlalchemy import select, text
from org_service.main import app
from org_service.models.user import User
from tests.utils.test_db import get_test_session
from org_service.routes.auth_routes import get_db


@pytest.fixture
def mock_oauth(mocker):
    mock = mocker.patch("org_service.services.auth_service.oauth")
    mock.google.authorize_access_token = mocker.AsyncMock()
    mock.google.parse_id_token = mocker.AsyncMock()
    return mock


@pytest.mark.asyncio
async def test_login_redirects_to_google():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        resp = await ac.get("/auth/login", follow_redirects=False)
    assert resp.status_code == status.HTTP_302_FOUND
    assert "accounts.google.com" in resp.headers["location"]


@pytest.mark.asyncio
async def test_callback_with_invalid_state_returns_400(async_client):
    response = await async_client.get("/auth/callback?state=bad&code=123")
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_callback_creates_user_if_not_exists(async_client, mock_oauth):
    # Patch dependency to ensure route uses test DB
    app.dependency_overrides[get_db] = get_test_session

    # Clear out test DB first
    session_maker = await get_test_session()
    async with session_maker as session:
        await session.execute(text("TRUNCATE users, accounts CASCADE"))
        await session.commit()
        await session.close()

    # Create mock user
    unique_email = f"newuser-{uuid.uuid4()}@example.com"
    mock_oauth.google.authorize_access_token.return_value = {
        "access_token": "fake-access-token"
    }
    mock_oauth.google.parse_id_token.return_value = {
        "sub": "newuser-sub",
        "email": unique_email,
        "name": "New User",
    }

    # Trigger route
    response = await async_client.get("/auth/callback?code=fakecode&state=fakestate")
    assert response.status_code == 200

    # ✅ Confirm user inserted in test DB
    session_maker = await get_test_session()
    async with session_maker as session:
        result = await session.execute(select(User).where(User.email == unique_email))
        user = result.scalar_one_or_none()
        assert user is not None
        assert user.email == unique_email

    # Clean up override
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_callback_does_not_create_user_if_exists(
    async_client, existing_user, db_session, mock_oauth
):
    mock_oauth.google.authorize_access_token.return_value = {
        "access_token": "fake-access-token"
    }
    mock_oauth.google.parse_id_token.return_value = {
        "sub": existing_user.google_sub,
        "email": existing_user.email,
        "name": existing_user.full_name,
    }

    response = await async_client.get("/auth/callback?code=fakecode&state=fakestate")
    assert response.status_code == 200

    # ✅ Confirm no duplicate user was created
    result = await db_session.execute(
        select(User).where(User.email == existing_user.email)
    )
    users = result.scalars().all()
    assert len(users) == 1


# 🔜 Future: Add test for missing email/sub in parse_id_token
# 🔜 Future: Add test for OAuth failure (bad token or raise error)
