import asyncio
import time
import uuid
import warnings
import subprocess

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from jose import jwt
from unittest.mock import AsyncMock

from org_service.config import settings
from org_service.main import app
from org_service.models.account import Account
from org_service.models.user import User
from tests.utils.test_db import get_test_engine, get_test_session
from sqlalchemy.exc import SAWarning


# -- Silence pooled connection cleanup warnings
def pytest_configure(config):
    warnings.filterwarnings(
        "ignore", category=SAWarning, message=".*non-checked-in connection.*"
    )


# -- Run Alembic migrations on the test DB
@pytest.fixture(scope="session", autouse=True)
def apply_migrations():
    subprocess.run(["alembic", "upgrade", "head"], check=True)


# -- Event Loop & AnyIO backend
@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# -- Async DB session fixture
@pytest_asyncio.fixture(scope="function", autouse=True)
async def db_session():
    engine = get_test_engine()

    async with get_test_session() as session:
        yield session
        await session.rollback()

    await engine.dispose()


# -- Dependency override for FastAPI get_db
def get_db():
    raise NotImplementedError

@pytest_asyncio.fixture(autouse=True)
async def override_get_db(db_session):
    async def _override():
        yield db_session
    app.dependency_overrides[get_db] = _override
    yield
    app.dependency_overrides.clear()


# -- HTTPX client for test requests
@pytest_asyncio.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


# -- Mock Google OAuth service
@pytest.fixture
def mock_oauth(mocker):
    mock = mocker.patch("org_service.services.auth_service.oauth")
    mock.google.authorize_access_token = AsyncMock()
    mock.google.parse_id_token = AsyncMock()
    return mock


# -- Existing user fixture
@pytest_asyncio.fixture
async def existing_user(db_session):
    account_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    unique_email = f"existing-{uuid.uuid4()}@example.com"

    account = Account(account_id=account_id)
    user = User(
        user_id=user_id,
        account_id=account_id,
        email=unique_email,
        full_name="Existing User",
        google_sub=f"sub-{user_id}",
    )
    db_session.add_all([account, user])
    await db_session.commit()
    return user


# -- Valid JWT token fixture
@pytest.fixture
def valid_jwt_token():
    now = int(time.time())
    payload = {
        "sub": "test-user-id",
        "account_id": "test-account-id",
        "roles": ["admin"],
        "email": "test@example.com",
        "exp": now + 3600,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
