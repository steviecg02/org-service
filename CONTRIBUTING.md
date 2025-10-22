# Contributing to org-service

This document outlines the development standards, patterns, and workflows for the org-service authentication microservice.

---

## Table of Contents

- [Development Environment Setup](#development-environment-setup)
- [Code Standards](#code-standards)
- [FastAPI Architecture Patterns](#fastapi-architecture-patterns)
- [Security Patterns](#security-patterns)
- [Testing Requirements](#testing-requirements)
- [Development Workflow](#development-workflow)
- [Make Commands Reference](#make-commands-reference)
- [Troubleshooting](#troubleshooting)

---

## Development Environment Setup

### Prerequisites

- **Python 3.11+**
- **PostgreSQL 15+** (or use Docker)
- **Docker & Docker Compose** (recommended)
- **Git**

### Initial Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd org-service
   ```

2. **Create virtual environment:**
   ```bash
   make venv
   source venv/bin/activate
   ```

3. **Configure environment variables:**

   Create a `.env` file in the project root:
   ```env
   # Database
   DATABASE_URL=postgresql://postgres:postgres@localhost:5432/org_service

   # Google OAuth (get from Google Cloud Console)
   GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your-client-secret
   GOOGLE_OAUTH_REDIRECT_URI=http://localhost:8000/auth/callback

   # JWT Configuration
   JWT_SECRET_KEY=your-super-secret-jwt-key-min-32-chars
   JWT_ALGORITHM=HS256
   JWT_EXPIRY_SECONDS=86400
   ```

   **IMPORTANT:**
   - `JWT_SECRET_KEY` must be long (32+ characters) and random
   - Never commit `.env` to version control
   - Test database will automatically use `{DATABASE_NAME}_test` suffix

4. **Start PostgreSQL (via Docker):**
   ```bash
   docker-compose up -d db
   ```

5. **Run Alembic migrations:**
   ```bash
   alembic upgrade head
   ```

6. **Install pre-commit hooks:**
   ```bash
   pre-commit install
   ```

7. **Run the development server:**
   ```bash
   make dev
   ```

   The API will be available at `http://localhost:8000`
   - API docs: `http://localhost:8000/docs`
   - OpenAPI spec: `http://localhost:8000/openapi.json`

---

## Code Standards

### Type Hints (Required)

All functions must have complete type hints for parameters and return values.

```python
from __future__ import annotations
from fastapi import Request
from pydantic import BaseModel

async def get_user(
    request: Request,
    user_id: str
) -> dict[str, Any]:
    """Fetch user from database."""
    ...
```

**Rules:**
- Use `from __future__ import annotations` for clean syntax
- All function parameters must have type hints
- All return types must be specified
- Use `dict[str, Any]`, `list[str]` (not `Dict`, `List` from typing)

### Docstrings (Required - Google Style)

All public functions, classes, and routes need docstrings.

```python
@router.get("/users/{user_id}")
async def get_user_by_id(user_id: str, request: Request) -> UserOut:
    """
    Get user by ID.

    Args:
        user_id: UUID of user to fetch
        request: FastAPI request (contains authenticated user context)

    Returns:
        User object with id, email, roles

    Raises:
        HTTPException: 404 if user not found
        HTTPException: 403 if user doesn't have permission
    """
    ...
```

**Required sections:**
- Description (1-2 sentences)
- Args: All parameters with descriptions
- Returns: What the function returns
- Raises: All exceptions that may be raised

### Code Formatting

**Black** (line length: 88)
- All code must be formatted with Black
- Pre-commit hook enforces this automatically

**Ruff** (linting)
- Must pass all Ruff checks
- Pre-commit hook enforces this

**MyPy** (type checking)
- Must pass MyPy type checks
- Uses SQLAlchemy plugin for model type checking

**Run formatting manually:**
```bash
make format    # Runs black + ruff --fix
make lint      # Runs all pre-commit hooks
```

### Logging

**Use Python `logging` module - NO `print()` statements**

```python
import logging

logger = logging.getLogger(__name__)

# Include structured context
logger.info(
    "User logged in",
    extra={
        "user_id": user_id,
        "account_id": account_id,
        "method": "google_oauth"
    }
)

# Log security events
logger.warning(
    "JWT validation failed",
    extra={
        "reason": "expired_token",
        "path": request.url.path
    }
)
```

**Log levels:**
- `DEBUG`: Detailed diagnostic information
- `INFO`: General informational messages
- `WARNING`: Warning messages (e.g., deprecated usage)
- `ERROR`: Error messages
- `CRITICAL`: Critical failures

---

## FastAPI Architecture Patterns

### Layered Structure (Non-Negotiable)

```
org_service/
├── main.py                      # FastAPI app, lifespan, middleware
├── routes/
│   ├── auth_routes.py           # OAuth, login, callback
│   └── secure_routes.py         # Protected endpoints (require JWT)
├── middleware/
│   └── jwt_middleware.py        # JWT validation, attach request.state.user
├── services/
│   └── auth_service.py          # Business logic (create user, get roles, etc.)
├── models/
│   ├── user.py                  # SQLAlchemy Core table definitions
│   └── account.py
├── schemas/
│   ├── user.py                  # Pydantic request/response models (TO BE CREATED)
│   └── account.py
├── db.py                        # Database connection
├── config.py                    # Settings (Pydantic)
└── logging_config.py
```

### 1. No Business Logic in Route Handlers

Routes should be "dumb" - extract parameters, call services, return responses.

```python
# ❌ BAD - Business logic in route handler
@router.post("/users")
async def create_user(user_data: UserCreate):
    # Direct database access in route
    async with engine.begin() as conn:
        result = await conn.execute(...)
    # Complex business logic in route
    if something:
        do_thing()
    return result

# ✅ GOOD - Route calls service layer
@router.post("/users")
async def create_user(user_data: UserCreate):
    """Create new user (delegates to service)."""
    user = await auth_service.create_user(user_data)
    return user
```

### 2. Service Layer Contains Business Logic

```python
# services/auth_service.py
async def create_user(user_data: UserCreate) -> User:
    """
    Create new user and account.

    Business logic:
    - Check if user exists
    - Create account if needed
    - Assign default role (Owner)
    - Send welcome email (future)
    """
    async with engine.begin() as conn:
        # Check existing
        existing = await conn.execute(...)
        if existing:
            raise ValueError("User exists")

        # Create user
        await conn.execute(...)

        # Assign role
        await conn.execute(...)

    return user
```

### 3. Pydantic Models for Request/Response

**TO BE IMPLEMENTED:** Create `schemas/` directory with Pydantic models.

```python
# schemas/user.py
from pydantic import BaseModel, EmailStr
from uuid import UUID

class UserCreate(BaseModel):
    """Request model for creating user."""
    email: EmailStr
    password: str

class UserOut(BaseModel):
    """Response model for user data."""
    id: UUID
    email: EmailStr
    account_id: UUID
    roles: list[str]
    created_at: str

    class Config:
        from_attributes = True  # For SQLAlchemy compatibility
```

### 4. SQLAlchemy Core (NOT ORM)

Use SQLAlchemy Core with raw SQL or `text()`:

```python
from sqlalchemy import text

# ✅ GOOD - Raw SQL with parameters
async with engine.begin() as conn:
    result = await conn.execute(
        text("""
            SELECT * FROM users
            WHERE account_id = :account_id
        """),
        {"account_id": account_id}
    )
    users = [dict(row._mapping) for row in result]
```

**Why not ORM?**
- More explicit and predictable
- Better performance
- Easier to audit security (multi-tenancy)

### 5. Alembic for ALL Migrations

**NEVER** create tables programmatically. Always use Alembic migrations.

```bash
# Create migration
alembic revision --autogenerate -m "add users table"

# Review the generated migration file before applying!

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

**Important:**
- Always review auto-generated migrations before applying
- Test migrations on a copy of production data before deploying
- Never edit applied migration files

---

## Security Patterns

**CRITICAL:** This service implements authentication/authorization patterns that will be reused across all microservices.

For detailed security pattern implementations, see `SECURITY-PATTERNS.md` in the repository root.

### JWT Authentication (Pattern 1)

**Key requirements:**
- Extract `Authorization: Bearer <token>` header
- Validate JWT signature and expiry
- On success: attach `request.state.user` dict
- On failure: return 401 Unauthorized
- Log all security events

**Implementation:** `org_service/middleware/jwt_middleware.py`

### Multi-Tenancy (Pattern 2)

**CRITICAL RULE:** EVERY database query MUST filter by `account_id`.

```python
# ✅ CORRECT - Always scope by account_id
async def get_user_data(request: Request):
    account_id = request.state.user["account_id"]

    result = await conn.execute(
        text("SELECT * FROM data WHERE account_id = :account_id"),
        {"account_id": account_id}
    )

# ❌ DANGEROUS - No account_id filter
async def get_all_data():
    result = await conn.execute(text("SELECT * FROM data"))
    # SECURITY BREACH - Returns data from ALL accounts
```

### Role-Based Access Control (Pattern 4)

```python
def require_role(required_roles: list[str]):
    """Decorator to enforce role-based access control."""
    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            user_roles = request.state.user.get("roles", [])

            if not any(role in user_roles for role in required_roles):
                raise HTTPException(
                    status_code=403,
                    detail=f"Requires one of: {required_roles}"
                )

            return await func(request, *args, **kwargs)
        return wrapper
    return decorator

@router.delete("/users/{user_id}")
@require_role(["admin", "owner"])
async def delete_user(user_id: str, request: Request):
    """Delete user (admin/owner only)."""
    ...
```

### Public vs Protected Endpoints

```python
# Public endpoints (no JWT required) - configured in main.py
PUBLIC_PATHS = [
    "/docs",
    "/openapi.json",
    "/auth/login",
    "/auth/callback",
    "/health"
]

# Protected endpoints (JWT required)
# All other routes require valid JWT
```

---

## Testing Requirements

### Coverage Targets

- **Minimum Overall:** 80%
- **Core Modules:** 90% (middleware, services, routes)

### Test Types

1. **Unit tests:** Services, utilities (mocked dependencies)
2. **Integration tests:** Routes with real DB, mocked external APIs
3. **Security tests:** JWT validation, multi-tenancy isolation

### Running Tests

```bash
# Run all tests
make test

# Run with coverage report
pytest --cov=org_service --cov-report=html

# Run specific test file
pytest tests/routes/test_auth_routes.py -v

# Run specific test
pytest tests/routes/test_auth_routes.py::test_login_redirect -v
```

### Writing Tests

**Test protected routes:**
```python
async def test_protected_route_requires_jwt(async_client):
    """Protected route returns 401 without JWT."""
    response = await async_client.get("/users/me")
    assert response.status_code == 401

async def test_protected_route_accepts_valid_jwt(async_client, valid_jwt_token):
    """Protected route accepts valid JWT."""
    headers = {"Authorization": f"Bearer {valid_jwt_token}"}
    response = await async_client.get("/users/me", headers=headers)
    assert response.status_code == 200
```

**Test multi-tenancy isolation:**
```python
async def test_users_isolated_by_account(async_client, user_account_a, user_account_b):
    """Users can only see data from their own account."""
    # User A's JWT
    jwt_a = create_jwt(user_account_a)
    headers = {"Authorization": f"Bearer {jwt_a}"}

    response = await async_client.get("/users", headers=headers)
    users = response.json()

    # Should only contain users from account A
    for user in users:
        assert user["account_id"] == user_account_a.account_id
```

### Test Fixtures

Common fixtures are defined in `tests/conftest.py`:
- `db_session`: Async database session (auto-rollback)
- `async_client`: HTTPX async client for API testing
- `mock_oauth`: Mocked Google OAuth service
- `existing_user`: Pre-created test user
- `valid_jwt_token`: Valid JWT for testing protected routes

---

## Development Workflow

### Starting a Feature

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make changes** following code standards

3. **Run tests:**
   ```bash
   make test
   ```

4. **Run linters:**
   ```bash
   make lint
   ```

5. **Commit changes:**
   ```bash
   git add .
   git commit -m "Add feature: description"
   ```

   Pre-commit hooks will automatically run black, ruff, mypy.

### Pull Request Requirements

**Before submitting a PR:**

- [ ] All tests pass (`make test`)
- [ ] Code coverage meets targets (80%+ overall, 90%+ for core modules)
- [ ] All linters pass (`make lint`)
- [ ] Type hints on all functions
- [ ] Docstrings on all public functions
- [ ] No business logic in route handlers
- [ ] All database queries filter by `account_id` (if applicable)
- [ ] Security events are logged
- [ ] New features have tests (unit + integration)

**PR template:**
```markdown
## Description
[What does this PR do?]

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed

## Security Considerations
- [ ] Multi-tenancy isolation verified
- [ ] Authentication/authorization tested
- [ ] Security events logged

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Tests pass locally
- [ ] Documentation updated
```

### Commit Message Format

Use conventional commit format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `refactor`: Code refactoring
- `test`: Adding/updating tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(auth): add Microsoft OAuth support

Implements OAuth flow for Microsoft Azure AD authentication.
Follows same pattern as Google OAuth.

Closes #123
```

```
fix(jwt): validate token expiry correctly

Previously, expired tokens were accepted due to incorrect
timestamp comparison. Now properly rejects expired tokens.
```

---

## Make Commands Reference

```bash
make help            # Show all available commands

# Setup
make install         # Install prod dependencies
make install-dev     # Install dev + prod dependencies
make venv            # Create and initialize virtualenv

# Development
make dev             # Run development server with auto-reload

# Docker
make build           # Build Docker image
make shell           # Run interactive container with mounted code

# Testing
make test            # Run all tests with pytest
make test-container  # Run tests inside Docker container

# Code Quality
make lint            # Run all linters (via pre-commit)
make format          # Format code (black + ruff)

# Cleanup
make clean           # Remove __pycache__, .pyc files, caches
```

---

## Troubleshooting

### Alembic Issues

**Error: "Table already exists"**

This happens when tables were created programmatically instead of via migrations.

**Solution:**
```bash
# Drop and recreate database
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;

# Re-run migrations
alembic upgrade head
```

**Error: "Can't locate revision"**

Usually indicates migration file corruption or missing files.

**Solution:**
```bash
# Check migration history
alembic current
alembic history

# If corrupted, may need to:
# 1. Drop all tables
# 2. Delete alembic/versions/*.py
# 3. Recreate initial migration
alembic revision --autogenerate -m "initial schema"
alembic upgrade head
```

### JWT Validation Failures

**Error: "Invalid token"**

Check:
1. Token is properly formatted: `Bearer <token>`
2. `JWT_SECRET_KEY` matches between token generation and validation
3. Token has not expired (check `exp` claim)
4. Token contains required claims: `sub`, `account_id`, `email`, `roles`

**View token contents:**
```python
from jose import jwt
token = "your-token-here"
decoded = jwt.decode(token, options={"verify_signature": False})
print(decoded)
```

### Test Database Issues

**Error: "Database does not exist"**

The test database is created automatically, but if you encounter this:

```bash
# Manually create test database
createdb org_service_test

# Run migrations on test DB
alembic upgrade head
```

**Error: "Relation already exists"**

Test fixtures may not be cleaning up properly.

**Solution:**
```bash
# Reset test database
dropdb org_service_test
createdb org_service_test
alembic upgrade head
```

### Google OAuth Issues

**Error: "State mismatch"**

This occurs when the OAuth state parameter doesn't match between redirect and callback.

**Causes:**
- Cookies cleared between redirect and callback
- Multiple concurrent login attempts
- User already logged in with Google

**Solution:**
- Use incognito/private browsing mode
- Clear cookies and try again
- Ensure `SessionMiddleware` is configured in `main.py`

---

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [SQLAlchemy Core Documentation](https://docs.sqlalchemy.org/en/20/core/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SECURITY-PATTERNS.md](./SECURITY-PATTERNS.md) - Reusable security patterns

---

## Questions?

For questions or issues, please:
1. Check this CONTRIBUTING.md
2. Review existing issues
3. Create a new issue with detailed description
