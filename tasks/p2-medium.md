# P2 - Medium Priority Tasks

**Priority:** Future Sprint (2-4 weeks)

**Estimated Time:** 16-20 hours

---

## 1. Complete Type Hints on All Functions

**Current Status:** ~40% of functions have complete type hints

**Missing Type Hints:**

### org_service/routes/auth_routes.py
```python
# Current
@router.get("/login")
async def login(request: Request):
    ...

# Should be
from fastapi.responses import RedirectResponse

@router.get("/login")
async def login(request: Request) -> RedirectResponse:
    ...

# Current
@router.get("/callback")
async def auth_callback(request: Request, db: AsyncSession = Depends(get_db)):
    ...

# Should be
@router.get("/callback")
async def auth_callback(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> dict[str, str]:
    ...
```

### org_service/middleware/jwt_middleware.py
```python
# Current
async def dispatch(self, request: Request, call_next):
    ...

# Should be
from starlette.responses import Response

async def dispatch(self, request: Request, call_next) -> Response:
    ...
```

**Steps:**
1. Add type hints to all route handlers
2. Add type hints to middleware methods
3. Run mypy to verify:
   ```bash
   mypy org_service/
   ```
4. Fix any type errors
5. Update mypy.ini to enable strict mode

**Acceptance Criteria:**
- [ ] All functions have return type hints
- [ ] mypy passes with no errors
- [ ] Strict mode enabled in mypy.ini

---

## 2. Improve Error Logging with Structured Context

**Current Issue:** Logging uses f-strings and lacks context

**Files to Update:**
- org_service/middleware/jwt_middleware.py
- org_service/services/auth_service.py

### jwt_middleware.py
```python
# Current (line 44)
except JWTError as e:
    logger.warning(f"JWT validation failed: {e}")
    return JSONResponse(status_code=401, content={"detail": "Invalid token"})

# Should be
except JWTError as e:
    logger.warning(
        "JWT validation failed",
        extra={
            "error": str(e),
            "error_type": type(e).__name__,
            "path": request.url.path,
            "method": request.method,
            "has_auth_header": "Authorization" in request.headers
        },
        exc_info=True
    )
    return JSONResponse(status_code=401, content={"detail": "Invalid token"})
```

### auth_service.py
```python
# Current (line 51-52)
logger.warning("OAuth callback failed: mismatching state")

# Should be
logger.warning(
    "OAuth callback failed",
    extra={
        "reason": "mismatching_state",
        "has_session_nonce": "nonce" in request.session,
        "callback_url": str(request.url)
    }
)

# Current (line 62)
logger.error("Incomplete user info from Google")

# Should be
logger.error(
    "Incomplete user info from Google",
    extra={
        "has_sub": bool(google_sub),
        "has_email": bool(email),
        "has_name": bool(name),
        "userinfo_keys": list(userinfo.keys())
    }
)

# Current (line 82, 84)
logger.info(f"Created new user: {email}")
logger.info(f"Existing user found: {email}")

# Should be
logger.info(
    "Created new user",
    extra={
        "user_id": str(user.user_id),
        "account_id": str(account.account_id),
        "email": email
    }
)

logger.info(
    "Existing user login",
    extra={
        "user_id": str(user.user_id),
        "account_id": str(user.account_id),
        "email": email
    }
)
```

**Acceptance Criteria:**
- [ ] All logger calls use structured logging (extra dict)
- [ ] Include relevant context (user_id, account_id, error details)
- [ ] No f-strings in log messages
- [ ] PII handled carefully (email logged sparingly)

---

## 3. Add Multi-Tenancy Isolation Tests

**Current Issue:** No tests verify account_id isolation

**Steps:**

### Create tests/test_multi_tenancy.py
```python
"""Tests for multi-tenancy isolation."""

import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from org_service.main import app
from org_service.models.account import Account
from org_service.models.user import User
from org_service.utils.jwt import create_jwt_token

@pytest.mark.asyncio
async def test_user_cannot_access_other_account_data(db_session):
    """Users can only access data from their own account."""
    # Create two accounts
    account_a_id = str(uuid.uuid4())
    account_b_id = str(uuid.uuid4())

    account_a = Account(account_id=account_a_id)
    account_b = Account(account_id=account_b_id)
    db_session.add_all([account_a, account_b])
    await db_session.flush()

    # Create user in each account
    user_a = User(
        user_id=str(uuid.uuid4()),
        account_id=account_a_id,
        email=f"user_a_{uuid.uuid4()}@example.com",
        full_name="User A",
        google_sub=f"sub_a_{uuid.uuid4()}"
    )
    user_b = User(
        user_id=str(uuid.uuid4()),
        account_id=account_b_id,
        email=f"user_b_{uuid.uuid4()}@example.com",
        full_name="User B",
        google_sub=f"sub_b_{uuid.uuid4()}"
    )
    db_session.add_all([user_a, user_b])
    await db_session.commit()

    # Create JWT for user A
    token_a = create_jwt_token({
        "sub": str(user_a.user_id),
        "account_id": str(user_a.account_id),
        "email": user_a.email,
        "roles": ["member"]
    })

    # When user listing endpoint is implemented, test:
    # User A should NOT see User B in results

    # For now, verify JWT contains correct account_id
    from org_service.utils.jwt import decode_jwt_token
    decoded = decode_jwt_token(token_a)
    assert decoded["account_id"] == str(user_a.account_id)
    assert decoded["account_id"] != str(user_b.account_id)


@pytest.mark.asyncio
async def test_jwt_contains_account_id(async_client, existing_user):
    """JWT token contains account_id claim."""
    token = create_jwt_token({
        "sub": str(existing_user.user_id),
        "account_id": str(existing_user.account_id),
        "email": existing_user.email,
        "roles": ["member"]
    })

    headers = {"Authorization": f"Bearer {token}"}
    response = await async_client.get("/secure/whoami", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert "account_id" in data["user"]
    assert data["user"]["account_id"] == str(existing_user.account_id)
```

**NOTE:** These tests will become more important when data query endpoints are added. For now, they verify the foundation is correct.

**Acceptance Criteria:**
- [ ] Multi-tenancy test file created
- [ ] Tests verify account_id in JWT
- [ ] Tests prepared for future data endpoints
- [ ] Document multi-tenancy requirements

---

## 4. Add Service Layer Unit Tests

**Current Issue:** 0% coverage on services/auth_service.py

**Steps:**

### Create tests/services/test_auth_service.py
```python
"""Unit tests for auth service."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException
from org_service.services.auth_service import handle_google_callback

@pytest.mark.asyncio
async def test_handle_google_callback_with_incomplete_userinfo(mocker):
    """Callback with missing email raises HTTPException."""
    # Mock OAuth
    mock_oauth = mocker.patch("org_service.services.auth_service.oauth")
    mock_oauth.google.authorize_access_token = AsyncMock(return_value={})
    mock_oauth.google.parse_id_token = AsyncMock(return_value={
        "sub": "test-sub",
        # Missing email and name
    })

    # Mock request
    mock_request = MagicMock()
    mock_request.session = {"nonce": "test-nonce"}

    # Mock database
    mock_db = AsyncMock()

    # Should raise HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await handle_google_callback(mock_request, mock_db)

    assert exc_info.value.status_code == 400
    assert "Invalid Google response" in exc_info.value.detail


@pytest.mark.asyncio
async def test_handle_google_callback_creates_account_for_new_user(mocker, db_session):
    """New user gets a new account created."""
    # Mock OAuth
    mock_oauth = mocker.patch("org_service.services.auth_service.oauth")
    mock_oauth.google.authorize_access_token = AsyncMock(return_value={})
    mock_oauth.google.parse_id_token = AsyncMock(return_value={
        "sub": "new-sub",
        "email": "new@example.com",
        "name": "New User"
    })

    # Mock request
    mock_request = MagicMock()
    mock_request.session = {"nonce": "test-nonce"}

    # Call service
    token = await handle_google_callback(mock_request, db_session)

    # Verify token returned
    assert isinstance(token, str)
    assert len(token) > 0

    # Verify user and account created
    from sqlalchemy import select
    from org_service.models.user import User

    result = await db_session.execute(
        select(User).where(User.email == "new@example.com")
    )
    user = result.scalar_one_or_none()
    assert user is not None
    assert user.account_id is not None
```

### Test JWT Utility Functions

Create tests/utils/test_jwt.py:
```python
"""Tests for JWT utilities."""

import pytest
import time
from jose import jwt, JWTError
from org_service.utils.jwt import create_jwt_token, decode_jwt_token
from org_service.config import settings

def test_create_jwt_token_includes_expiry():
    """JWT token includes expiry claim."""
    token = create_jwt_token({
        "sub": "test-user",
        "account_id": "test-account"
    })

    decoded = jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm]
    )

    assert "exp" in decoded
    assert decoded["exp"] > time.time()


def test_create_jwt_token_with_custom_expiry():
    """JWT token respects custom expiry."""
    token = create_jwt_token(
        {"sub": "test"},
        expiry_seconds=10
    )

    decoded = jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm]
    )

    # Expiry should be ~10 seconds from now
    assert decoded["exp"] - time.time() < 15


def test_decode_jwt_token_validates_signature():
    """Decode raises error on invalid signature."""
    token = create_jwt_token({"sub": "test"})

    # Tamper with token
    parts = token.split(".")
    tampered = ".".join([parts[0], parts[1], "invalid"])

    with pytest.raises(JWTError):
        decode_jwt_token(tampered)


def test_decode_jwt_token_rejects_expired():
    """Decode raises error on expired token."""
    token = create_jwt_token(
        {"sub": "test"},
        expiry_seconds=-1  # Already expired
    )

    with pytest.raises(JWTError):
        decode_jwt_token(token)
```

**Acceptance Criteria:**
- [ ] Service layer tests created
- [ ] JWT utility tests created
- [ ] Edge cases covered (missing data, errors)
- [ ] Coverage >80% on auth_service.py
- [ ] Coverage >90% on utils/jwt.py

---

## 5. Create .env.example File

**Issue:** Environment variables not documented

**Steps:**

Create .env.example:
```env
# Database
# PostgreSQL connection string
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/org_service

# Google OAuth Configuration
# Get these from Google Cloud Console: https://console.cloud.google.com/
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_OAUTH_REDIRECT_URI=http://localhost:8000/auth/callback

# JWT Configuration
# Generate a secure random key: openssl rand -hex 32
JWT_SECRET_KEY=your-super-secret-jwt-key-minimum-32-characters-long
JWT_ALGORITHM=HS256
JWT_EXPIRY_SECONDS=86400

# Development Settings
# Uvicorn will use these if present
# UVICORN_HOST=0.0.0.0
# UVICORN_PORT=8000
# UVICORN_RELOAD=true

# Production Settings (uncomment for production)
# JWT_EXPIRY_SECONDS=3600
# DATABASE_URL=postgresql://prod_user:prod_password@db.example.com:5432/org_service_prod
```

Add to .gitignore (should already be there):
```
.env
.env.*
```

Update README.md to reference .env.example:
```markdown
### Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
# Edit .env with your actual values
```

See `.env.example` for all available configuration options.
```

**Acceptance Criteria:**
- [ ] .env.example created
- [ ] All required variables documented
- [ ] Example values provided
- [ ] Security notes included
- [ ] README references .env.example

---

## 6. Add pyproject.toml for Tool Configuration

**Issue:** Tool configurations scattered across multiple files

**Steps:**

Create pyproject.toml:
```toml
[project]
name = "org-service"
version = "0.1.0"
description = "Authentication and organizational identity microservice"
requires-python = ">=3.11"

[tool.black]
line-length = 88
target-version = ["py311"]
include = '\.pyi?$'
exclude = '''
/(
    \.git
  | \.mypy_cache
  | \.pytest_cache
  | \.ruff_cache
  | venv
  | build
  | dist
  | alembic/versions
)/
'''

[tool.ruff]
line-length = 88
target-version = "py311"

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
]
ignore = [
    "E501",  # line too long (handled by black)
    "B008",  # function calls in argument defaults (FastAPI Depends)
]

[tool.ruff.lint.per-file-ignores]
"__init__.py" = ["F401"]  # Unused imports ok in __init__
"alembic/versions/*.py" = ["F401"]  # Alembic migrations

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
plugins = ["sqlalchemy.ext.mypy.plugin"]

[[tool.mypy.overrides]]
module = "authlib.*"
ignore_missing_imports = true

[[tool.mypy.overrides]]
module = "jose.*"
ignore_missing_imports = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
asyncio_mode = "auto"
markers = [
    "slow: marks tests as slow",
    "integration: marks tests as integration tests",
]

[tool.coverage.run]
source = ["org_service"]
omit = [
    "*/tests/*",
    "*/alembic/*",
]

[tool.coverage.report]
precision = 2
show_missing = true
skip_covered = false
```

Update mypy.ini (can keep or migrate to pyproject.toml):
- If keeping mypy.ini, ensure settings match pyproject.toml
- If migrating, delete mypy.ini

**Acceptance Criteria:**
- [ ] pyproject.toml created
- [ ] Black configuration migrated
- [ ] Ruff configuration added
- [ ] MyPy configuration migrated
- [ ] Pytest configuration added
- [ ] Coverage configuration added
- [ ] All tools work with new config

---

## 7. Add Rate Limiting

**Issue:** No protection against brute force or DoS attacks

**Steps:**

### Install slowapi
Add to requirements.txt:
```
slowapi
```

### Configure rate limiting in main.py
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Create limiter
limiter = Limiter(key_func=get_remote_address)

# Create app with limiter
app = FastAPI(middleware=middleware)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

### Add rate limits to auth routes
```python
from slowapi import Limiter
from fastapi import Request

# Get limiter from app state
def get_limiter():
    from org_service.main import limiter
    return limiter

@router.get("/login")
@get_limiter().limit("10/minute")
async def login(request: Request):
    ...

@router.get("/callback")
@get_limiter().limit("20/minute")
async def auth_callback(request: Request, db: AsyncSession = Depends(get_db)):
    ...
```

### Test rate limiting
Create tests/test_rate_limiting.py:
```python
import pytest
from httpx import AsyncClient, ASGITransport
from org_service.main import app

@pytest.mark.asyncio
async def test_login_rate_limit():
    """Login endpoint has rate limit."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        # Make 11 requests (limit is 10/minute)
        for i in range(11):
            response = await ac.get("/auth/login", follow_redirects=False)
            if i < 10:
                assert response.status_code in [302, 200]
            else:
                # 11th request should be rate limited
                assert response.status_code == 429
```

**Acceptance Criteria:**
- [ ] slowapi installed
- [ ] Rate limiting configured
- [ ] Auth endpoints have limits
- [ ] Tests verify rate limiting
- [ ] Documentation updated

---

## Summary

After completing P2 tasks, the service will have:
- ✅ Complete type hints everywhere
- ✅ Structured logging with context
- ✅ Multi-tenancy isolation tests
- ✅ Service layer test coverage
- ✅ .env.example for easy setup
- ✅ Consolidated tool configuration
- ✅ Rate limiting protection

**Estimated Total Time:** 16-20 hours

**Next:** Move to P3 tasks in `tasks/p3-low.md`
