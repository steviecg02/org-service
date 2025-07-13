import asyncio
import asyncpg
import os
import pytest_asyncio
import pytest
import time
import uuid
import warnings
from httpx import AsyncClient, ASGITransport
from jose import jwt
from unittest.mock import AsyncMock
from urllib.parse import urlparse

from sqlalchemy.exc import SAWarning
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from org_service.config import settings
from org_service.main import app
from org_service.models.base import Base
from org_service.models.account import Account
from org_service.models.user import User

TEST_DB_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/org_service_test"


def pytest_configure(config):
    warnings.filterwarnings(
        "ignore", category=SAWarning, message=".*non-checked-in connection.*"
    )


# --- Ensure test DB exists ---
async def ensure_test_db():
    db_url = os.getenv("DATABASE_URL", TEST_DB_URL)
    parsed = urlparse(db_url)

    test_db = parsed.path.lstrip("/")
    admin_url = db_url.replace("postgresql+asyncpg://", "postgresql://").replace(
        test_db, "postgres"
    )

    conn = await asyncpg.connect(dsn=admin_url)
    try:
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname=$1", test_db
        )
        if not exists:
            await conn.execute(f'CREATE DATABASE "{test_db}"')
    finally:
        await conn.close()


@pytest.fixture(scope="session", autouse=True)
def initialize_test_db():
    """Ensure test DB exists before session starts (run in correct event loop)."""
    asyncio.run(ensure_test_db())


# --- Event Loop & AnyIO ---
@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# --- Async DB Session ---
@pytest_asyncio.fixture(scope="function", autouse=True)
async def db_session():
    engine = create_async_engine(TEST_DB_URL, echo=False, future=True)
    session_maker = async_sessionmaker(
        bind=engine, expire_on_commit=False, class_=AsyncSession
    )

    # Clean schema before test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # Yield session
    async with session_maker() as session:
        yield session

        # Rollback any leftover state
        await session.rollback()

    # Dispose engine to fully reset between tests
    await engine.dispose()


# --- get_db override for FastAPI ---
def get_db():
    """Stub to satisfy override; this will be overridden in tests."""
    raise NotImplementedError


@pytest_asyncio.fixture(autouse=True)
async def override_get_db(db_session):
    async def _override():
        yield db_session

    app.dependency_overrides[get_db] = _override
    yield
    app.dependency_overrides.clear()


# --- Async Client for test requests ---
@pytest_asyncio.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


# --- OAuth Mock ---
@pytest.fixture
def mock_oauth(mocker):
    mock = mocker.patch("org_service.services.auth_service.oauth")
    mock.google.authorize_access_token = AsyncMock()
    mock.google.parse_id_token = AsyncMock()
    return mock


# --- Existing User Fixture ---
@pytest_asyncio.fixture
async def existing_user(db_session):
    account_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())

    account = Account(account_id=account_id)
    user = User(
        user_id=user_id,
        email="existing@example.com",
        account_id=account_id,
        full_name="Existing User",
        google_sub="existing-user-sub",
    )
    db_session.add_all([account, user])
    await db_session.commit()
    return user


# --- JWT Token Fixture ---
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
    return jwt.encode(
        payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )
