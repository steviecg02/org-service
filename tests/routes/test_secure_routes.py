import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from org_service.main import app
from org_service.utils.jwt import create_jwt_token


def get_valid_user_payload(overrides: dict = {}) -> dict:
    """
    Return a valid user payload for testing JWT generation.
    """
    return {
        "sub": str(uuid.uuid4()),
        "email": "test@example.com",
        "account_id": str(uuid.uuid4()),
        "roles": ["user"],
        **overrides,
    }


@pytest.mark.asyncio
async def test_whoami_returns_user_info():
    payload = get_valid_user_payload()
    token = create_jwt_token(payload)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        resp = await ac.get(
            "/secure/whoami", headers={"Authorization": f"Bearer {token}"}
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["user"]["user_id"] == payload["sub"]
    assert data["user"]["email"] == payload["email"]


@pytest.mark.asyncio
async def test_whoami_with_valid_token_returns_user():
    payload = get_valid_user_payload()
    token = create_jwt_token(payload)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        resp = await ac.get(
            "/secure/whoami", headers={"Authorization": f"Bearer {token}"}
        )

    assert resp.status_code == 200
    assert resp.json()["user"]["email"] == payload["email"]


@pytest.mark.asyncio
async def test_whoami_without_token_returns_401():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        resp = await ac.get("/secure/whoami")

    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_whoami_with_malformed_token_returns_401():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        resp = await ac.get(
            "/secure/whoami", headers={"Authorization": "Bearer malformed.token"}
        )

    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_whoami_with_expired_token_returns_401():
    payload = get_valid_user_payload()
    token = create_jwt_token(payload, expiry_seconds=-1)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        resp = await ac.get(
            "/secure/whoami", headers={"Authorization": f"Bearer {token}"}
        )

    assert resp.status_code == 401
