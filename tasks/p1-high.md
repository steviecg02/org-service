# P1 - High Priority Tasks

**Priority:** Next Sprint (1-2 weeks)

**Estimated Time:** 12-16 hours

---

## 1. Create Pydantic Schemas Directory

**Issue:** No schemas/ directory - routes return raw dicts

**Benefits:**
- Type-safe request/response models
- Automatic validation
- OpenAPI documentation
- Standardized response format

**Steps:**

### 1.1 Create Directory Structure
```bash
mkdir -p org_service/schemas
touch org_service/schemas/__init__.py
```

### 1.2 Create schemas/user.py
```python
"""Pydantic schemas for user requests/responses."""

from __future__ import annotations
from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from datetime import datetime

class UserBase(BaseModel):
    """Base user fields."""
    email: EmailStr
    full_name: str

class UserCreate(UserBase):
    """Schema for creating a user (future email/password auth)."""
    password: str = Field(min_length=8)

class UserOut(BaseModel):
    """Schema for user response."""
    user_id: UUID
    account_id: UUID
    email: EmailStr
    full_name: str
    roles: list[str]
    created_at: datetime

    class Config:
        from_attributes = True  # For SQLAlchemy compatibility
        json_encoders = {
            UUID: str,  # Serialize UUIDs as strings
            datetime: lambda v: v.isoformat()
        }

class UserContext(BaseModel):
    """Schema for request.state.user context."""
    user_id: UUID
    account_id: UUID
    email: EmailStr
    roles: list[str]
```

### 1.3 Create schemas/account.py
```python
"""Pydantic schemas for account requests/responses."""

from __future__ import annotations
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class AccountOut(BaseModel):
    """Schema for account response."""
    account_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }
```

### 1.4 Update schemas/__init__.py
```python
"""Pydantic schemas for API requests/responses."""

from org_service.schemas.user import UserOut, UserCreate, UserContext
from org_service.schemas.account import AccountOut

__all__ = ["UserOut", "UserCreate", "UserContext", "AccountOut"]
```

### 1.5 Update secure_routes.py
```python
from fastapi import APIRouter, Request
from org_service.schemas import UserOut

router = APIRouter(prefix="/secure", tags=["secure"])

@router.get("/whoami", response_model=UserOut)
async def whoami(request: Request) -> UserOut:
    """
    Returns current user context from JWT.

    Args:
        request: FastAPI request with user context

    Returns:
        UserOut: Current user information
    """
    return UserOut(**request.state.user)
```

### 1.6 Test Changes
```bash
# Run tests
pytest tests/routes/test_secure_routes.py -v

# Verify response is properly serialized
# Check /docs to see improved OpenAPI docs
```

**Acceptance Criteria:**
- [ ] schemas/ directory created
- [ ] UserOut, UserCreate, AccountOut defined
- [ ] secure_routes.py uses response_model
- [ ] Tests pass
- [ ] /docs shows proper response schemas

---

## 2. Implement Proper Role Assignment Logic

**Issue:** All users get hardcoded "owner" role

**Current Code (auth_service.py:89):**
```python
token_data = {
    "sub": str(user.user_id),
    "account_id": str(user.account_id),
    "roles": ["owner"],  # TODO: Replace with actual role resolution
    "email": user.email,
}
```

**Requirements:**
- First user in account = "owner" role
- Subsequent users = "member" role
- Create user_roles table for many-to-many relationship

**Steps:**

### 2.1 Create Alembic Migration for user_roles Table
```bash
alembic revision -m "add user_roles table"
```

Edit migration file:
```python
def upgrade():
    op.create_table(
        'user_roles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.user_id'), nullable=False),
        sa.Column('account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('accounts.account_id'), nullable=False),
        sa.Column('role_name', sa.String, nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint('user_id', 'account_id', 'role_name', name='uq_user_account_role')
    )
    op.create_index('idx_user_roles_user_id', 'user_roles', ['user_id'])
    op.create_index('idx_user_roles_account_id', 'user_roles', ['account_id'])

def downgrade():
    op.drop_index('idx_user_roles_account_id')
    op.drop_index('idx_user_roles_user_id')
    op.drop_table('user_roles')
```

Apply migration:
```bash
alembic upgrade head
```

### 2.2 Create models/user_role.py
```python
"""User role model for account-scoped roles."""

import uuid
from sqlalchemy import Column, String, DateTime, func, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from .base import Base

class UserRole(Base):
    """Represents a role assigned to a user within an account."""

    __tablename__ = "user_roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False
    )
    account_id = Column(
        UUID(as_uuid=True), ForeignKey("accounts.account_id"), nullable=False
    )
    role_name = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint('user_id', 'account_id', 'role_name', name='uq_user_account_role'),
    )
```

### 2.3 Update services/auth_service.py

Add role assignment logic:
```python
from sqlalchemy import select, func as sql_func
from org_service.models.user_role import UserRole

async def handle_google_callback(request: Request, db: AsyncSession) -> str:
    # ... existing OAuth code ...

    if not user:
        account = Account()
        db.add(account)
        await db.flush()

        user = User(
            google_sub=google_sub,
            email=email,
            full_name=name,
            account_id=account.account_id,
        )
        db.add(user)
        await db.flush()

        # Assign "owner" role to first user
        user_role = UserRole(
            user_id=user.user_id,
            account_id=account.account_id,
            role_name="owner"
        )
        db.add(user_role)
        await db.commit()

        logger.info(f"Created new user with owner role: {email}")

        roles = ["owner"]
    else:
        # Get existing user's roles
        result = await db.execute(
            select(UserRole.role_name).where(
                UserRole.user_id == user.user_id,
                UserRole.account_id == user.account_id
            )
        )
        roles = [row[0] for row in result.fetchall()]

        logger.info(f"Existing user found: {email}, roles: {roles}")

    token_data = {
        "sub": str(user.user_id),
        "account_id": str(user.account_id),
        "roles": roles,
        "email": user.email,
    }

    return create_jwt_token(token_data)
```

### 2.4 Test Changes
```bash
pytest tests/routes/test_auth_routes.py -v
```

**Acceptance Criteria:**
- [ ] user_roles table created
- [ ] UserRole model defined
- [ ] First user gets "owner" role
- [ ] Subsequent users get roles from database
- [ ] Tests pass

---

## 3. Implement @require_role() Decorator

**Issue:** No role enforcement on protected routes

**Steps:**

### 3.1 Create org_service/decorators/__init__.py
```python
"""Decorators for route protection."""
```

### 3.2 Create org_service/decorators/rbac.py
```python
"""Role-based access control decorators."""

from __future__ import annotations
from functools import wraps
from fastapi import HTTPException, Request
from org_service.logging_config import logger

def require_role(allowed_roles: list[str]):
    """
    Decorator to enforce role-based access control.

    Args:
        allowed_roles: List of role names that can access the route

    Raises:
        HTTPException: 403 if user doesn't have required role

    Example:
        @router.delete("/users/{user_id}")
        @require_role(["admin", "owner"])
        async def delete_user(user_id: str, request: Request):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            user_roles = request.state.user.get("roles", [])

            if not any(role in allowed_roles for role in user_roles):
                logger.warning(
                    "Access denied - insufficient permissions",
                    extra={
                        "user_id": request.state.user["user_id"],
                        "user_roles": user_roles,
                        "required_roles": allowed_roles,
                        "path": request.url.path
                    }
                )
                raise HTTPException(
                    status_code=403,
                    detail=f"Forbidden. Requires one of: {', '.join(allowed_roles)}"
                )

            return await func(request, *args, **kwargs)
        return wrapper
    return decorator
```

### 3.3 Add Example Protected Route

Add to secure_routes.py:
```python
from org_service.decorators.rbac import require_role

@router.delete("/users/{user_id}")
@require_role(["admin", "owner"])
async def delete_user(user_id: str, request: Request):
    """
    Delete user (admin/owner only).

    Args:
        user_id: UUID of user to delete
        request: Request with user context

    Raises:
        HTTPException: 403 if not admin/owner
        HTTPException: 404 if user not found
    """
    # Implementation would go here
    return {"status": "deleted", "user_id": user_id}
```

### 3.4 Create Tests

Add to tests/routes/test_secure_routes.py:
```python
async def test_delete_user_requires_owner_role(async_client):
    """Delete user endpoint requires owner role."""
    # Create JWT with member role
    token = create_jwt_token({
        "sub": str(uuid.uuid4()),
        "account_id": str(uuid.uuid4()),
        "email": "member@example.com",
        "roles": ["member"]
    })

    headers = {"Authorization": f"Bearer {token}"}
    response = await async_client.delete("/secure/users/some-id", headers=headers)

    assert response.status_code == 403
    assert "Forbidden" in response.json()["detail"]

async def test_delete_user_allows_owner_role(async_client):
    """Delete user endpoint allows owner role."""
    token = create_jwt_token({
        "sub": str(uuid.uuid4()),
        "account_id": str(uuid.uuid4()),
        "email": "owner@example.com",
        "roles": ["owner"]
    })

    headers = {"Authorization": f"Bearer {token}"}
    response = await async_client.delete("/secure/users/some-id", headers=headers)

    assert response.status_code == 200
```

**Acceptance Criteria:**
- [ ] @require_role() decorator created
- [ ] Decorator checks user roles from JWT
- [ ] Returns 403 if insufficient permissions
- [ ] Logs access denials
- [ ] Tests verify role enforcement

---

## 4. Delete Duplicate models.py from Root

**Issue:** Old duplicate file can cause import confusion

**File:** `/Users/sguilfoil/Git/org-service/models.py`

**Steps:**

1. Verify no imports reference it:
   ```bash
   grep -r "import models" org_service/
   grep -r "from models import" org_service/
   ```

2. If any imports found, update them to use org_service.models

3. Delete file:
   ```bash
   rm /Users/sguilfoil/Git/org-service/models.py
   ```

4. Run tests:
   ```bash
   pytest -v
   ```

5. Commit:
   ```bash
   git rm models.py
   git commit -m "chore: remove duplicate models.py from root"
   ```

**Acceptance Criteria:**
- [ ] No imports reference root models.py
- [ ] File deleted
- [ ] Tests still pass
- [ ] Committed to git

---

## 5. Add Health Check Endpoint

**Issue:** No /health endpoint for container orchestration

**Steps:**

### 5.1 Create routes/health_routes.py
```python
"""Health check endpoints for monitoring."""

from __future__ import annotations
from fastapi import APIRouter
from sqlalchemy import text
from org_service.db import engine

router = APIRouter(tags=["health"])

@router.get("/health")
async def health_check() -> dict[str, str]:
    """
    Health check endpoint.

    Returns:
        dict: Health status and database connectivity

    Example:
        {"status": "ok", "database": "connected"}
    """
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return {
        "status": "ok" if db_status == "connected" else "degraded",
        "database": db_status
    }
```

### 5.2 Register Router in main.py
```python
from org_service.routes import auth_routes, secure_routes, health_routes

# ... existing code ...

app.include_router(health_routes.router)
```

### 5.3 Add /health to Exempt Paths
```python
# main.py
Middleware(
    JWTMiddleware,
    exempt_paths=[
        "/auth/login",
        "/auth/callback",
        "/docs",
        "/openapi.json",
        "/favicon.ico",
        "/health",  # Add this
    ],
),
```

### 5.4 Test
```bash
# Manual test
curl http://localhost:8000/health

# Expected: {"status": "ok", "database": "connected"}

# Add test
pytest tests/routes/test_health_routes.py -v
```

Create tests/routes/test_health_routes.py:
```python
import pytest
from httpx import AsyncClient, ASGITransport
from org_service.main import app

@pytest.mark.asyncio
async def test_health_check_returns_ok():
    """Health check returns ok when database connected."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        response = await ac.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["ok", "degraded"]
    assert "database" in data

@pytest.mark.asyncio
async def test_health_check_does_not_require_jwt():
    """Health check endpoint does not require JWT."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        # No Authorization header
        response = await ac.get("/health")

    assert response.status_code == 200
```

**Acceptance Criteria:**
- [ ] /health endpoint created
- [ ] Returns database status
- [ ] Does not require JWT
- [ ] Tests verify functionality
- [ ] Documented in README

---

## Summary

After completing P1 tasks, the service will have:
- ✅ Pydantic schemas for type-safe APIs
- ✅ Proper role assignment (owner for first user)
- ✅ Role-based access control enforcement
- ✅ Clean codebase (no duplicates)
- ✅ Health check for monitoring

**Estimated Total Time:** 12-16 hours

**Next:** Move to P2 tasks in `tasks/p2-medium.md`
