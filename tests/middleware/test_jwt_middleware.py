import pytest
from org_service.utils.jwt import create_jwt_token


@pytest.mark.asyncio
async def test_jwt_middleware_accepts_valid_token(async_client, existing_user):
    token = create_jwt_token(
        {
            "sub": str(existing_user.user_id),
            "account_id": str(existing_user.account_id),
            "email": existing_user.email,
            "roles": ["user"],
        }
    )
    headers = {"Authorization": f"Bearer {token}"}
    response = await async_client.get("/secure/whoami", headers=headers)
    assert response.status_code == 200
    assert response.json()["user"]["email"] == existing_user.email


@pytest.mark.asyncio
async def test_jwt_middleware_rejects_invalid_token(async_client):
    headers = {"Authorization": "Bearer invalid.token.here"}
    response = await async_client.get("/secure/whoami", headers=headers)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_jwt_middleware_requires_token(async_client):
    response = await async_client.get("/secure/whoami")
    assert response.status_code == 401
