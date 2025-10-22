# P3 - Low Priority Tasks

**Priority:** Nice to Have (1-3 months)

**Estimated Time:** 20-30 hours

---

## 1. Add Request ID Middleware

**Benefit:** Trace requests across logs for debugging

**Steps:**

### Create org_service/middleware/request_id.py
```python
"""Middleware to add unique request ID to each request."""

from __future__ import annotations
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from org_service.logging_config import logger

class RequestIDMiddleware(BaseHTTPMiddleware):
    """Add unique request ID to each request."""

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Generate request ID and attach to request state.

        Args:
            request: Incoming request
            call_next: Next middleware in chain

        Returns:
            Response with X-Request-ID header
        """
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        logger.info(
            "Request started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path
            }
        )

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        logger.info(
            "Request completed",
            extra={
                "request_id": request_id,
                "status_code": response.status_code
            }
        )

        return response
```

### Register in main.py
```python
from org_service.middleware.request_id import RequestIDMiddleware

middleware = [
    Middleware(RequestIDMiddleware),  # Add first
    Middleware(SessionMiddleware, secret_key=settings.jwt_secret_key),
    Middleware(JWTMiddleware, exempt_paths=[...]),
]
```

### Update logging to include request_id
Modify logging_config.py to include request_id in all logs:
```python
import logging
from contextvars import ContextVar

request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)

class RequestIDFilter(logging.Filter):
    """Add request ID to log records."""

    def filter(self, record):
        record.request_id = request_id_var.get() or "no-request-id"
        return True

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(request_id)s] %(message)s",
)

logger = logging.getLogger("org_service")
logger.addFilter(RequestIDFilter())
```

**Acceptance Criteria:**
- [ ] Request ID middleware created
- [ ] X-Request-ID header returned
- [ ] Request ID in all log messages
- [ ] Tests verify request ID

---

## 2. Improve API Documentation

**Benefit:** Better auto-generated docs for API consumers

**Steps:**

### Add descriptions to FastAPI app
```python
# main.py
app = FastAPI(
    title="org-service",
    description="""
    Authentication and organizational identity microservice.

    ## Features

    * **Google OAuth Login** - Authenticate via Google
    * **JWT Authentication** - Secure API access with JWT tokens
    * **Multi-Tenancy** - Account-scoped data isolation
    * **Role-Based Access Control** - Granular permissions

    ## Authentication

    Most endpoints require a JWT token in the Authorization header:

    ```
    Authorization: Bearer <your-jwt-token>
    ```

    To get a token, use the `/auth/login` flow.
    """,
    version="0.1.0",
    contact={
        "name": "Your Team",
        "email": "team@example.com",
    },
    license_info={
        "name": "MIT",
    },
)
```

### Add response examples to Pydantic schemas
```python
# schemas/user.py
class UserOut(BaseModel):
    """Schema for user response."""
    user_id: UUID
    account_id: UUID
    email: EmailStr
    full_name: str
    roles: list[str]
    created_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "account_id": "123e4567-e89b-12d3-a456-426614174001",
                "email": "user@example.com",
                "full_name": "John Doe",
                "roles": ["member"],
                "created_at": "2025-01-15T10:30:00Z"
            }
        }
```

### Add route descriptions and tags
```python
# routes/auth_routes.py
@router.get(
    "/login",
    summary="Initiate Google OAuth Login",
    description="""
    Redirects to Google OAuth login page.

    After successful authentication, user will be redirected to `/auth/callback`
    with authorization code.
    """,
    responses={
        302: {"description": "Redirect to Google OAuth"},
    }
)
async def login(request: Request) -> RedirectResponse:
    ...

@router.get(
    "/callback",
    summary="OAuth Callback Handler",
    description="""
    Handles OAuth callback from Google.

    Creates user and account on first login, returns JWT token.
    """,
    responses={
        200: {
            "description": "JWT token issued successfully",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "token_type": "bearer"
                    }
                }
            }
        },
        400: {"description": "Invalid OAuth state or response"},
    }
)
async def auth_callback(...):
    ...
```

**Acceptance Criteria:**
- [ ] FastAPI app has description
- [ ] All schemas have examples
- [ ] All routes have summaries and descriptions
- [ ] Response examples documented
- [ ] /docs looks professional

---

## 3. Add CI/CD Pipeline

**Benefit:** Automated testing and quality checks on PRs

**Steps:**

### Create .github/workflows/ci.yml
```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt -r dev-requirements.txt

      - name: Run black
        run: black --check org_service/ tests/

      - name: Run ruff
        run: ruff check org_service/ tests/

      - name: Run mypy
        run: mypy org_service/

  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: timescale/timescaledb:2.13.1-pg15
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: org_service_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt -r dev-requirements.txt

      - name: Run migrations
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/org_service_test
        run: alembic upgrade head

      - name: Run tests
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/org_service
          GOOGLE_CLIENT_ID: test-client-id
          GOOGLE_CLIENT_SECRET: test-secret
          GOOGLE_OAUTH_REDIRECT_URI: http://localhost:8000/auth/callback
          JWT_SECRET_KEY: test-jwt-secret-key-for-ci-only
        run: pytest -v --cov=org_service --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          fail_ci_if_error: false
```

### Create .github/workflows/docker.yml
```yaml
name: Docker Build

on:
  push:
    branches: [main]
    tags: ["v*"]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2

      - name: Build image
        run: docker build -t org-service:latest .

      - name: Test image
        run: |
          docker run --rm org-service:latest python -c "import org_service; print('OK')"
```

**Acceptance Criteria:**
- [ ] CI workflow runs on PRs
- [ ] Linting enforced
- [ ] Tests run automatically
- [ ] Docker build verified
- [ ] Coverage uploaded to Codecov

---

## 4. Implement Account Management Endpoints

**Benefit:** CRUD operations for accounts

**Steps:**

### Create routes/account_routes.py
```python
"""Account management endpoints."""

from __future__ import annotations
from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from org_service.services.auth_service import get_db
from org_service.schemas import AccountOut
from org_service.models.account import Account
from org_service.decorators.rbac import require_role
from org_service.logging_config import logger

router = APIRouter(prefix="/accounts", tags=["accounts"])

@router.get("/{account_id}", response_model=AccountOut)
async def get_account(
    account_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> AccountOut:
    """
    Get account by ID.

    Args:
        account_id: UUID of account
        request: Request with user context
        db: Database session

    Returns:
        Account information

    Raises:
        HTTPException: 403 if user doesn't belong to account
        HTTPException: 404 if account not found
    """
    # Verify user belongs to this account
    user_account_id = request.state.user["account_id"]
    if user_account_id != account_id:
        logger.warning(
            "Access denied - account mismatch",
            extra={
                "user_id": request.state.user["user_id"],
                "user_account_id": user_account_id,
                "requested_account_id": account_id
            }
        )
        raise HTTPException(
            status_code=403,
            detail="Forbidden - cannot access other accounts"
        )

    result = await db.execute(
        select(Account).where(Account.account_id == account_id)
    )
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    return AccountOut.from_orm(account)


@router.get("/{account_id}/users")
@require_role(["admin", "owner"])
async def list_account_users(
    account_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    List all users in account (admin/owner only).

    Args:
        account_id: UUID of account
        request: Request with user context
        db: Database session

    Returns:
        List of users in account

    Raises:
        HTTPException: 403 if not admin/owner or wrong account
    """
    # Verify user belongs to this account
    user_account_id = request.state.user["account_id"]
    if user_account_id != account_id:
        raise HTTPException(status_code=403, detail="Forbidden")

    # Query users
    result = await db.execute(
        text("SELECT * FROM users WHERE account_id = :account_id"),
        {"account_id": account_id}
    )

    users = [dict(row._mapping) for row in result]
    return {"users": users}
```

### Add tests
```python
# tests/routes/test_account_routes.py
async def test_get_account_returns_own_account(async_client, existing_user):
    """User can get their own account."""
    token = create_jwt_token({
        "sub": str(existing_user.user_id),
        "account_id": str(existing_user.account_id),
        "email": existing_user.email,
        "roles": ["member"]
    })

    headers = {"Authorization": f"Bearer {token}"}
    response = await async_client.get(
        f"/accounts/{existing_user.account_id}",
        headers=headers
    )

    assert response.status_code == 200
    assert response.json()["account_id"] == str(existing_user.account_id)


async def test_get_account_rejects_other_account(async_client, existing_user):
    """User cannot get other account."""
    other_account_id = str(uuid.uuid4())

    token = create_jwt_token({
        "sub": str(existing_user.user_id),
        "account_id": str(existing_user.account_id),
        "email": existing_user.email,
        "roles": ["member"]
    })

    headers = {"Authorization": f"Bearer {token}"}
    response = await async_client.get(
        f"/accounts/{other_account_id}",
        headers=headers
    )

    assert response.status_code == 403
```

**Acceptance Criteria:**
- [ ] GET /accounts/{id} implemented
- [ ] GET /accounts/{id}/users implemented
- [ ] Multi-tenancy enforced (can only access own account)
- [ ] Role enforcement on sensitive endpoints
- [ ] Tests verify security

---

## 5. Implement User Management Endpoints

**Benefit:** CRUD operations for users

**Steps:**

### Add to routes/user_routes.py
```python
"""User management endpoints."""

from __future__ import annotations
from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from org_service.services.auth_service import get_db
from org_service.schemas import UserOut
from org_service.models.user import User
from org_service.decorators.rbac import require_role
from org_service.logging_config import logger

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", response_model=UserOut)
async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> UserOut:
    """
    Get current user from JWT.

    Args:
        request: Request with user context
        db: Database session

    Returns:
        Current user information
    """
    user_id = request.state.user["user_id"]

    result = await db.execute(
        select(User).where(User.user_id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserOut(
        user_id=user.user_id,
        account_id=user.account_id,
        email=user.email,
        full_name=user.full_name,
        roles=request.state.user["roles"],
        created_at=user.created_at
    )


@router.get("/", response_model=list[UserOut])
async def list_users(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> list[UserOut]:
    """
    List all users in current user's account.

    Args:
        request: Request with user context
        db: Database session

    Returns:
        List of users in same account
    """
    account_id = request.state.user["account_id"]

    # CRITICAL: Filter by account_id for multi-tenancy
    result = await db.execute(
        select(User).where(User.account_id == account_id)
    )
    users = result.scalars().all()

    return [
        UserOut(
            user_id=user.user_id,
            account_id=user.account_id,
            email=user.email,
            full_name=user.full_name,
            roles=[],  # TODO: Load from user_roles table
            created_at=user.created_at
        )
        for user in users
    ]


@router.delete("/{user_id}")
@require_role(["admin", "owner"])
async def delete_user(
    user_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete user (admin/owner only).

    Args:
        user_id: UUID of user to delete
        request: Request with user context
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException: 403 if not admin/owner
        HTTPException: 404 if user not found
        HTTPException: 400 if trying to delete self
    """
    # Prevent self-deletion
    if user_id == request.state.user["user_id"]:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")

    account_id = request.state.user["account_id"]

    # Verify user belongs to same account
    result = await db.execute(
        select(User).where(
            User.user_id == user_id,
            User.account_id == account_id  # Multi-tenancy check
        )
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await db.delete(user)
    await db.commit()

    logger.info(
        "User deleted",
        extra={
            "deleted_user_id": user_id,
            "deleted_by": request.state.user["user_id"],
            "account_id": account_id
        }
    )

    return {"status": "deleted", "user_id": user_id}
```

**Acceptance Criteria:**
- [ ] GET /users/me implemented
- [ ] GET /users implemented with account_id filter
- [ ] DELETE /users/{id} implemented
- [ ] Role enforcement on delete
- [ ] Multi-tenancy verified in tests

---

## 6. Add Structured Logging with JSON Format

**Benefit:** Better log parsing in production

**Steps:**

### Install python-json-logger
Add to requirements.txt:
```
python-json-logger
```

### Update logging_config.py
```python
"""Centralized logger configuration with JSON formatting."""

import logging
import sys
from pythonjsonlogger import jsonlogger

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional fields."""

    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        log_record['level'] = record.levelname
        log_record['logger'] = record.name
        log_record['service'] = 'org-service'

# Create handler
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(CustomJsonFormatter(
    '%(asctime)s %(level)s %(logger)s %(message)s'
))

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    handlers=[handler]
)

logger = logging.getLogger("org_service")
```

Example log output:
```json
{
  "asctime": "2025-01-15 10:30:00,123",
  "level": "INFO",
  "logger": "org_service",
  "message": "User logged in",
  "service": "org-service",
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "account_id": "123e4567-e89b-12d3-a456-426614174001",
  "method": "google_oauth"
}
```

**Acceptance Criteria:**
- [ ] JSON logging installed
- [ ] All logs output as JSON
- [ ] Structured context preserved
- [ ] Production-ready log format

---

## Summary

P3 tasks are enhancements that improve developer experience and production readiness but are not critical for initial deployment.

**Total Estimated Time:** 20-30 hours

**Priority Order:**
1. Request ID middleware (debugging)
2. API documentation (developer experience)
3. CI/CD pipeline (automation)
4. Account/user management (features)
5. JSON logging (production observability)

**After P3:** Service is fully production-ready with comprehensive features and observability.
