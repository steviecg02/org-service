# Code Quality Debt

Technical debt and code quality improvements identified in the audit.

---

## 1. Complete Type Hints

**Priority:** P2
**Estimated Time:** 2-3 hours

**Files Missing Return Type Hints:**

### routes/auth_routes.py (lines 14, 32)
```python
# Current
@router.get("/login")
async def login(request: Request):

# Should be
from fastapi.responses import RedirectResponse

@router.get("/login")
async def login(request: Request) -> RedirectResponse:
```

```python
# Current
@router.get("/callback")
async def auth_callback(request: Request, db: AsyncSession = Depends(get_db)):

# Should be
@router.get("/callback")
async def auth_callback(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> dict[str, str]:
```

### routes/secure_routes.py (line 6)
```python
# Current
@router.get("/whoami")
async def whoami(request: Request):

# Should be
@router.get("/whoami")
async def whoami(request: Request) -> dict[str, Any]:
```

### middleware/jwt_middleware.py (line 23)
```python
# Current
async def dispatch(self, request: Request, call_next):

# Should be
from starlette.responses import Response

async def dispatch(self, request: Request, call_next) -> Response:
```

**Acceptance Criteria:**
- [ ] All functions have return type hints
- [ ] Run `mypy org_service/` with no errors
- [ ] Update mypy.ini to enable `disallow_untyped_defs = true`

---

## 2. Complete Docstrings

**Priority:** P2
**Estimated Time:** 2-3 hours

**Functions with Incomplete Docstrings:**

### routes/auth_routes.py

**login()** - Missing Args/Returns:
```python
@router.get("/login")
async def login(request: Request) -> RedirectResponse:
    """
    Redirects to Google OAuth login.

    Args:
        request: FastAPI request object (session used for nonce)

    Returns:
        RedirectResponse: Redirect to Google OAuth authorization page

    Raises:
        None
    """
```

**auth_callback()** - Missing detailed Args:
```python
@router.get("/callback")
async def auth_callback(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> dict[str, str]:
    """
    Handles the OAuth callback, creates user, returns JWT.

    Args:
        request: FastAPI request containing OAuth callback parameters
        db: SQLAlchemy async database session

    Returns:
        dict: Dictionary with 'access_token' and 'token_type' keys

    Raises:
        HTTPException: 400 if OAuth state invalid or userinfo incomplete
    """
```

### routes/secure_routes.py

**whoami()** - Missing Args/Returns:
```python
@router.get("/whoami")
async def whoami(request: Request) -> dict[str, Any]:
    """
    Returns current user context from JWT.

    Args:
        request: FastAPI request with JWT-authenticated user in request.state.user

    Returns:
        dict: Dictionary containing user information (user_id, account_id, email, roles)

    Raises:
        None: Protected by JWT middleware, returns 401 if no valid JWT
    """
```

### services/auth_service.py

**get_db()** - Missing Yields:
```python
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Async dependency to provide a database session.

    Yields:
        AsyncSession: SQLAlchemy async session for database operations

    Note:
        Session is automatically closed after request completion
    """
```

**Acceptance Criteria:**
- [ ] All public functions have complete Google-style docstrings
- [ ] All docstrings include Args, Returns, Raises sections
- [ ] Docstrings are clear and descriptive

---

## 3. Improve Structured Logging

**Priority:** P2
**Estimated Time:** 2-3 hours

**See details in:** `tasks/p2-medium.md` section 2

**Files to Update:**
- org_service/middleware/jwt_middleware.py
- org_service/services/auth_service.py

**Summary:**
- Replace f-string logging with structured extra dicts
- Include relevant context (user_id, account_id, error details)
- Add request_id when middleware implemented
- Handle PII carefully (don't over-log email addresses)

---

## 4. Remove Duplicate Base Declaration

**Priority:** P1
**Estimated Time:** 30 minutes

**Issue:** `Base` declared in both places:
- `org_service/db.py:17`
- `org_service/models/base.py`

**Solution:**

### Option 1: Use models/base.py (Recommended)
```python
# db.py - Remove Base declaration
from org_service.models.base import Base  # Import instead

# Keep:
engine: AsyncEngine = create_async_engine(DATABASE_URL, echo=False, future=True)
async_session_maker = async_sessionmaker(bind=engine, expire_on_commit=False)

# Remove:
# Base = declarative_base()  # DELETE THIS LINE
```

### Option 2: Use db.py Base
```python
# models/base.py - Delete this file entirely

# models/__init__.py - Import from db.py
from org_service.db import Base
from org_service.models.user import User
from org_service.models.account import Account
```

**Recommended:** Option 1 (use models/base.py) - cleaner separation

**Acceptance Criteria:**
- [ ] Only one Base declaration exists
- [ ] All models import from single source
- [ ] Tests pass
- [ ] No import errors

---

## 5. Standardize Import Order

**Priority:** P3
**Estimated Time:** 1 hour

**Use isort or ruff to organize imports:**

```python
# Standard library
from __future__ import annotations
import uuid
from datetime import datetime, timedelta
from typing import Any, AsyncGenerator

# Third-party
from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

# Local
from org_service.config import settings
from org_service.db import async_session_maker
from org_service.logging_config import logger
from org_service.models import User, Account
from org_service.utils.jwt import create_jwt_token
```

**Configure in pyproject.toml:**
```toml
[tool.ruff.lint.isort]
known-first-party = ["org_service"]
section-order = ["future", "standard-library", "third-party", "first-party", "local-folder"]
```

**Run:**
```bash
ruff check --select I --fix org_service/
```

**Acceptance Criteria:**
- [ ] All imports sorted consistently
- [ ] isort configuration in pyproject.toml
- [ ] Pre-commit hook includes isort

---

## 6. Add Missing __init__.py Exports

**Priority:** P3
**Estimated Time:** 1 hour

**Current Issue:** models/__init__.py exports models, but other __init__.py files are empty

**Improve imports:**

### org_service/__init__.py
```python
"""org-service - Authentication and organizational identity microservice."""

__version__ = "0.1.0"
```

### org_service/models/__init__.py (already good)
```python
"""Database models."""

from org_service.models.user import User
from org_service.models.account import Account

__all__ = ["User", "Account"]
```

### org_service/routes/__init__.py (create)
```python
"""API routes."""

from org_service.routes import auth_routes, secure_routes

__all__ = ["auth_routes", "secure_routes"]
```

### org_service/utils/__init__.py (create)
```python
"""Utility functions."""

from org_service.utils import jwt

__all__ = ["jwt"]
```

**Acceptance Criteria:**
- [ ] All __init__.py files have docstrings
- [ ] Public APIs exported via __all__
- [ ] Version defined in org_service/__init__.py

---

## 7. Add Type Stubs for Third-Party Libraries

**Priority:** P3
**Estimated Time:** 1 hour

**Current Issue:** mypy.ini has `ignore_missing_imports` for authlib and jose

**Better approach:** Install type stubs

```bash
pip install types-python-jose
# authlib may not have stubs, keep ignore_missing_imports for that
```

**Update mypy.ini:**
```ini
[mypy]
plugins = sqlalchemy.ext.mypy.plugin

[[tool.mypy.overrides]]
module = "authlib.*"
ignore_missing_imports = true

# Remove jose override if types-python-jose installed
```

**Acceptance Criteria:**
- [ ] Type stubs installed where available
- [ ] mypy configuration minimizes ignore_missing_imports
- [ ] No new type errors introduced

---

## 8. Improve Test Organization

**Priority:** P3
**Estimated Time:** 2 hours

**Current Issue:** Test files are organized but could use pytest marks

**Add pytest markers:**

### conftest.py
```python
def pytest_configure(config):
    config.addinivalue_line("markers", "unit: Unit tests with mocked dependencies")
    config.addinivalue_line("markers", "integration: Integration tests with real database")
    config.addinivalue_line("markers", "slow: Slow-running tests")
```

### Mark tests appropriately
```python
# tests/routes/test_auth_routes.py
@pytest.mark.integration
@pytest.mark.asyncio
async def test_callback_creates_user_if_not_exists(async_client, mock_oauth):
    ...

# tests/middleware/test_jwt_middleware.py
@pytest.mark.unit
@pytest.mark.asyncio
async def test_jwt_middleware_rejects_invalid_token(async_client):
    ...
```

### Run specific test types
```bash
pytest -m unit           # Run only unit tests
pytest -m integration    # Run only integration tests
pytest -m "not slow"     # Skip slow tests
```

**Acceptance Criteria:**
- [ ] Pytest markers configured
- [ ] All tests marked appropriately
- [ ] README documents test markers
- [ ] Makefile has targets for different test types

---

## 9. Add Code Complexity Checks

**Priority:** P3
**Estimated Time:** 1 hour

**Tool:** radon or flake8-complexity

**Add to dev-requirements.txt:**
```
radon
```

**Check complexity:**
```bash
radon cc org_service/ -a -nb
```

**Add to CI:**
```yaml
# .github/workflows/ci.yml
- name: Check code complexity
  run: radon cc org_service/ --min B --no-assert
```

**Acceptance Criteria:**
- [ ] Complexity checking tool installed
- [ ] Baseline complexity documented
- [ ] CI fails if complexity >10 (grade B)
- [ ] Complex functions refactored

---

## 10. Improve Error Messages

**Priority:** P2
**Estimated Time:** 2 hours

**Current Issue:** Some error messages are generic

**Improvements:**

### jwt_middleware.py
```python
# Current
return JSONResponse(status_code=401, content={"detail": "Unauthorized"})

# Better
return JSONResponse(
    status_code=401,
    content={
        "detail": "Missing or invalid Authorization header",
        "error_code": "MISSING_AUTH_HEADER"
    }
)

# Current
return JSONResponse(status_code=401, content={"detail": "Invalid token"})

# Better
return JSONResponse(
    status_code=401,
    content={
        "detail": "JWT token is invalid or expired",
        "error_code": "INVALID_JWT"
    }
)
```

### auth_service.py
```python
# Current
raise HTTPException(status_code=400, detail="Invalid Google response")

# Better
raise HTTPException(
    status_code=400,
    detail={
        "message": "Google OAuth response is incomplete",
        "error_code": "INCOMPLETE_OAUTH_RESPONSE",
        "missing_fields": [f for f in ["sub", "email", "name"] if not locals().get(f)]
    }
)
```

**Create error code constants:**
```python
# utils/errors.py
class ErrorCodes:
    """Standard error codes for API responses."""

    # Authentication errors
    MISSING_AUTH_HEADER = "MISSING_AUTH_HEADER"
    INVALID_JWT = "INVALID_JWT"
    EXPIRED_JWT = "EXPIRED_JWT"

    # OAuth errors
    OAUTH_STATE_MISMATCH = "OAUTH_STATE_MISMATCH"
    INCOMPLETE_OAUTH_RESPONSE = "INCOMPLETE_OAUTH_RESPONSE"

    # Authorization errors
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"
    ACCOUNT_MISMATCH = "ACCOUNT_MISMATCH"
```

**Acceptance Criteria:**
- [ ] All HTTPExceptions have descriptive messages
- [ ] Error codes added to responses
- [ ] Error codes documented in API docs
- [ ] Consistent error response format

---

## Summary

**Total Estimated Time for All Code Quality Debt:** 14-18 hours

**Priority Order:**
1. Remove duplicate Base (P1) - 30 min
2. Complete type hints (P2) - 2-3 hours
3. Complete docstrings (P2) - 2-3 hours
4. Improve structured logging (P2) - 2-3 hours
5. Improve error messages (P2) - 2 hours
6. Standardize imports (P3) - 1 hour
7. Add __init__.py exports (P3) - 1 hour
8. Add type stubs (P3) - 1 hour
9. Improve test organization (P3) - 2 hours
10. Add complexity checks (P3) - 1 hour

**After completion:** Codebase will be cleaner, more maintainable, and easier for new developers to understand.
