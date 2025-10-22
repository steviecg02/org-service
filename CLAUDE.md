# Claude Code Instructions for org-service

**Purpose:** Guide for Claude Code when working on org-service codebase

**Last Updated:** October 21, 2025

---

## Project Overview

**What This Is:**
Production-grade FastAPI microservice for **authentication and organizational identity management**.

**Key Capabilities:**
- Google OAuth login
- JWT-based authentication
- Multi-tenant account management
- Role-based access control (RBAC)

**Role in Architecture:**
Central authentication authority for multi-service ecosystem. Other microservices (sync-hostaway, sync-airbnb) depend on org-service for user authentication and authorization.

---

## Critical Documents (Read These First!)

**Before starting ANY task, read these documents in order:**

###  1. `/docs/implementation-status.md`
**Purpose:** Current state audit - what's implemented, what's missing, what's broken

**Read this to:**
- Understand what features exist
- Identify known issues
- Check coverage status
- See code quality audit results

**Key Sections:**
- Feature Completeness (what works)
- Security Audit Results (critical security issues)
- Recommendations by Priority (what to fix first)

### 2. `/ARCHITECTURE.md`
**Purpose:** High-level system design and architecture

**Read this to:**
- Understand system components
- See authentication flows
- Learn security model (multi-tenancy, RBAC)
- Understand key design decisions

**Key Sections:**
- System Architecture (component diagram)
- Authentication Flow (OAuth → JWT → API access)
- Security Model (multi-tenancy rules)
- Database Schema

### 3. `/CONTRIBUTING.md`
**Purpose:** Code standards, patterns, and development workflow

**Read this to:**
- Follow code standards (type hints, docstrings, formatting)
- Understand FastAPI patterns (routes → services → models)
- Learn security patterns (JWT, multi-tenancy, RBAC)
- See testing requirements

**Key Sections:**
- Code Standards (type hints, docstrings, logging)
- FastAPI Architecture Patterns (non-negotiable rules)
- Security Patterns (critical for this service)
- Testing Requirements

### 4. `/tasks/` Directory
**Purpose:** Organized work backlog by priority

**Files:**
- `p0-critical.md` - **URGENT** security/blocking issues
- `p1-high.md` - High-priority features
- `p2-medium.md` - Medium-priority improvements
- `p3-low.md` - Nice-to-have enhancements
- `missing-features.md` - Feature backlog
- `code-quality-debt.md` - Tech debt

**Read this to:**
- Find specific tasks to work on
- Understand implementation steps
- See acceptance criteria

---

## Before Starting Any Task

**Checklist:**

1. **[ ] Read implementation-status.md** - Understand current state
2. **[ ] Check if feature already exists** - Search codebase
3. **[ ] Review ARCHITECTURE.md** - Understand design
4. **[ ] Review CONTRIBUTING.md** - Follow standards
5. **[ ] Check tasks/ directory** - See if task already documented
6. **[ ] Create test database if needed** - `createdb org_service_test`
7. **[ ] Run tests to establish baseline** - `pytest -v`

---

## Architecture Patterns (Non-Negotiable)

### 1. Layered Architecture

```
Routes → Services → Models → Database
```

**Rules:**
- **Routes are thin** - Extract parameters, call services, return responses
- **Services contain business logic** - Validation, database operations, business rules
- **NO business logic in routes** - EVER
- **NO database queries in routes** - Delegate to services

**Example:**
```python
# ❌ WRONG - Business logic in route
@router.post("/users")
async def create_user(user_data: dict):
    async with engine.begin() as conn:
        result = await conn.execute(...)  # Database in route
    return result

# ✅ CORRECT - Route calls service
@router.post("/users")
async def create_user(user_data: UserCreate):
    user = await auth_service.create_user(user_data)
    return user
```

### 2. Pydantic for Request/Response

**⚠️ IMPORTANT:** Pydantic schemas not yet implemented - this is P1 task

**When implemented:**
- All request bodies use Pydantic models
- All responses use `response_model`
- Located in `schemas/` directory

```python
# Future pattern (not yet implemented)
from org_service.schemas import UserOut

@router.get("/users/me", response_model=UserOut)
async def get_current_user(...) -> UserOut:
    ...
```

### 3. SQLAlchemy Core (NOT ORM)

**Rules:**
- Use `text()` for raw SQL or Core select/insert
- NO ORM queries (no `session.query()`)
- NO ORM relationships
- All queries use async engine

**Example:**
```python
from sqlalchemy import select, text

# ✅ CORRECT - SQLAlchemy Core
async with engine.begin() as conn:
    result = await conn.execute(
        select(User).where(User.email == email)
    )
    user = result.scalar_one_or_none()

# ✅ ALSO CORRECT - Raw SQL with text()
result = await conn.execute(
    text("SELECT * FROM users WHERE email = :email"),
    {"email": email}
)
```

### 4. Alembic for ALL Migrations

**Rules:**
- **NEVER** create tables programmatically
- **NEVER** use `Base.metadata.create_all()`
- **ALWAYS** create migrations for schema changes
- **ALWAYS** review auto-generated migrations

**Workflow:**
```bash
# Create migration
alembic revision --autogenerate -m "add user_roles table"

# CRITICAL: Review the generated migration file

# Apply migration
alembic upgrade head
```

---

## Security Requirements (CRITICAL)

### 1. Multi-Tenancy - account_id Scoping

**⚠️ CRITICAL RULE:** EVERY database query MUST filter by `account_id`

**Why:** Prevent data leakage between accounts (tenants)

**Pattern:**
```python
# ✅ CORRECT - Always filter by account_id
async def list_users(request: Request):
    account_id = request.state.user["account_id"]

    result = await conn.execute(
        select(User).where(User.account_id == account_id)
    )

# ❌ DANGEROUS - No account_id filter
async def list_all_users():
    result = await conn.execute(select(User))
    # SECURITY BREACH - Returns users from ALL accounts
```

**Testing:**
- ALWAYS write tests for multi-tenancy isolation
- Create users in different accounts
- Verify cross-account access is blocked

### 2. JWT Authentication

**Current Implementation:**
- Middleware: `org_service/middleware/jwt_middleware.py`
- Utilities: `org_service/utils/jwt.py`

**Key Points:**
- JWT contains: sub, account_id, email, roles, exp
- Middleware attaches `request.state.user` on valid JWT
- Returns 401 on invalid/missing/expired JWT
- Public paths exempt from JWT check

**Accessing User Context:**
```python
@router.get("/protected")
async def protected_route(request: Request):
    user_id = request.state.user["user_id"]
    account_id = request.state.user["account_id"]
    roles = request.state.user["roles"]
    email = request.state.user["email"]
```

### 3. Role-Based Access Control

**⚠️ Status:** Roles in JWT but NO enforcement yet (P1 task)

**When implemented:**
```python
from org_service.decorators.rbac import require_role

@router.delete("/users/{user_id}")
@require_role(["admin", "owner"])
async def delete_user(user_id: str, request: Request):
    # Only admins/owners can execute this
    ...
```

### 4. Security Logging

**ALWAYS log security events:**
```python
# Login/logout
logger.info(
    "User logged in",
    extra={
        "user_id": user_id,
        "account_id": account_id,
        "method": "google_oauth"
    }
)

# Access denied
logger.warning(
    "Access denied - insufficient permissions",
    extra={
        "user_id": request.state.user["user_id"],
        "required_roles": required_roles,
        "user_roles": user_roles,
        "path": request.url.path
    }
)

# JWT failures
logger.warning(
    "JWT validation failed",
    extra={
        "error": str(e),
        "path": request.url.path
    }
)
```

---

## Code Standards (Enforced by Pre-Commit)

### 1. Type Hints (Required)

**ALL functions must have type hints:**
```python
from __future__ import annotations
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

async def get_user(
    request: Request,
    user_id: str,
    db: AsyncSession
) -> dict[str, Any]:
    ...
```

**Check:**
```bash
mypy org_service/
```

### 2. Docstrings (Google Style)

**ALL public functions must have docstrings:**
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
        HTTPException: 403 if user doesn't have permission to access
    """
    ...
```

### 3. Logging (NO print() statements!)

**Use logger, NOT print():**
```python
from org_service.logging_config import logger

# ❌ WRONG
print("User logged in:", user_id)

# ✅ CORRECT
logger.info("User logged in", extra={"user_id": user_id})
```

**⚠️ CRITICAL:** There is a `print()` statement at `org_service/routes/secure_routes.py:11` - this is a P0 security issue to fix.

### 4. Code Formatting

**Black** (line length: 88):
```bash
black org_service/ tests/
```

**Ruff** (linting):
```bash
ruff check org_service/ tests/
```

**Pre-commit** (runs both):
```bash
pre-commit run --all-files
```

---

## Common Patterns

### Creating a New Route

**Steps:**

1. **Create route handler** (thin):
```python
# routes/user_routes.py
from fastapi import APIRouter, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from org_service.services.auth_service import get_db
from org_service.schemas import UserOut

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/{user_id}", response_model=UserOut)
async def get_user(
    user_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> UserOut:
    """
    Get user by ID.

    Args:
        user_id: UUID of user to fetch
        request: Request with user context
        db: Database session

    Returns:
        User information

    Raises:
        HTTPException: 404 if user not found
        HTTPException: 403 if not authorized
    """
    user = await user_service.get_user(user_id, request.state.user, db)
    return user
```

2. **Create service function** (business logic):
```python
# services/user_service.py
from fastapi import HTTPException
from sqlalchemy import select

async def get_user(
    user_id: str,
    current_user: dict,
    db: AsyncSession
) -> User:
    """
    Get user by ID with authorization check.

    Args:
        user_id: User ID to fetch
        current_user: Current user from JWT
        db: Database session

    Returns:
        User object

    Raises:
        HTTPException: 404 if not found, 403 if wrong account
    """
    account_id = current_user["account_id"]

    # CRITICAL: Filter by account_id
    result = await db.execute(
        select(User).where(
            User.user_id == user_id,
            User.account_id == account_id  # Multi-tenancy
        )
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user
```

3. **Register router**:
```python
# main.py
from org_service.routes import user_routes

app.include_router(user_routes.router)
```

4. **Write tests**:
```python
# tests/routes/test_user_routes.py
async def test_get_user_returns_own_account_user(async_client, existing_user):
    """User can get users from their own account."""
    token = create_jwt_token({...})
    headers = {"Authorization": f"Bearer {token}"}

    response = await async_client.get(f"/users/{existing_user.user_id}", headers=headers)

    assert response.status_code == 200
    assert response.json()["user_id"] == str(existing_user.user_id)

async def test_get_user_blocks_other_account(async_client):
    """User cannot get users from other accounts."""
    # Create user in account A
    # Try to access with JWT from account B
    # Expect 404 or 403
    ...
```

### Creating a Database Migration

**Steps:**

1. **Modify model**:
```python
# models/user.py
class User(Base):
    # ... existing fields ...
    phone_number = Column(String, nullable=True)  # NEW FIELD
```

2. **Generate migration**:
```bash
alembic revision --autogenerate -m "add phone_number to users"
```

3. **Review migration** (CRITICAL):
```python
# alembic/versions/xxx_add_phone_number_to_users.py

def upgrade():
    op.add_column('users', sa.Column('phone_number', sa.String(), nullable=True))

def downgrade():
    op.drop_column('users', 'phone_number')
```

4. **Apply migration**:
```bash
alembic upgrade head
```

5. **Verify**:
```bash
alembic current  # Check current version
```

### Adding Tests

**Test Structure:**
```
tests/
├── conftest.py          # Shared fixtures
├── routes/              # Route integration tests
├── services/            # Service unit tests
├── middleware/          # Middleware tests
└── utils/               # Utility tests
```

**Common Fixtures** (from conftest.py):
- `db_session` - Async database session
- `async_client` - HTTPX async client for API testing
- `mock_oauth` - Mocked OAuth provider
- `existing_user` - Pre-created test user
- `valid_jwt_token` - Valid JWT for testing

**Running Tests:**
```bash
# All tests
pytest -v

# Specific file
pytest tests/routes/test_auth_routes.py -v

# Specific test
pytest tests/routes/test_auth_routes.py::test_login_redirects_to_google -v

# With coverage
pytest --cov=org_service --cov-report=html
```

---

## Testing Requirements

### Coverage Targets

- **Minimum Overall:** 80%
- **Core Modules:** 90% (middleware, services, routes)

### Test Types Required

1. **Unit Tests**
   - Services with mocked database
   - Utilities with no dependencies
   - Mock all external calls

2. **Integration Tests**
   - Routes with real database
   - Middleware with real requests
   - Mock only external APIs (Google OAuth)

3. **Security Tests**
   - Multi-tenancy isolation
   - JWT validation (valid, invalid, expired)
   - Role enforcement (when implemented)
   - Cross-account access blocked

**CRITICAL:** Always write multi-tenancy isolation tests when adding data query endpoints.

---

## Common Pitfalls to Avoid

### 1. Missing account_id Filter

**❌ WRONG:**
```python
# Missing account_id filter - SECURITY BREACH
result = await db.execute(select(User))
users = result.scalars().all()  # Returns ALL users from ALL accounts
```

**✅ CORRECT:**
```python
account_id = request.state.user["account_id"]
result = await db.execute(
    select(User).where(User.account_id == account_id)
)
```

### 2. Using print() Instead of logging

**❌ WRONG:**
```python
print("User logged in:", user_id)  # Bypasses logging controls
```

**✅ CORRECT:**
```python
logger.info("User logged in", extra={"user_id": user_id})
```

### 3. Business Logic in Routes

**❌ WRONG:**
```python
@router.post("/users")
async def create_user(email: str):
    # Validation in route
    if not email:
        raise HTTPException(...)

    # Database in route
    async with engine.begin() as conn:
        result = await conn.execute(...)
    return result
```

**✅ CORRECT:**
```python
@router.post("/users")
async def create_user(user_data: UserCreate):
    user = await auth_service.create_user(user_data)
    return user
```

### 4. Not Using Pydantic for Responses

**❌ CURRENT (to be fixed):**
```python
@router.get("/whoami")
async def whoami(request: Request):
    return {"user": request.state.user}  # Raw dict
```

**✅ FUTURE (P1 task):**
```python
@router.get("/whoami", response_model=UserOut)
async def whoami(request: Request) -> UserOut:
    return UserOut(**request.state.user)
```

### 5. Skipping Alembic Migrations

**❌ WRONG:**
```python
# Creating tables programmatically
async with engine.begin() as conn:
    await conn.run_sync(Base.metadata.create_all)
```

**✅ CORRECT:**
```bash
alembic revision --autogenerate -m "create tables"
alembic upgrade head
```

---

## Working with User's Instructions

### If User Says: "Add a new endpoint"

1. Check if endpoint exists (search codebase)
2. Read ARCHITECTURE.md for design patterns
3. Create route handler (thin)
4. Create service function (business logic)
5. Add Pydantic schema (if needed)
6. Add multi-tenancy filtering (if data query)
7. Write tests (unit + integration + security)
8. Run tests: `pytest -v`
9. Check coverage: `pytest --cov=org_service`

### If User Says: "Fix security issue"

1. Read implementation-status.md Security Audit
2. Identify specific issue
3. Check CONTRIBUTING.md Security Patterns
4. Implement fix following patterns
5. Write security test to prevent regression
6. Run all tests
7. Log security event properly

### If User Says: "Add database table"

1. Create model in `models/`
2. Create Pydantic schema in `schemas/` (P1 task)
3. Create Alembic migration
4. Review migration file
5. Apply migration: `alembic upgrade head`
6. Write tests using new table
7. Document in ARCHITECTURE.md (Database Schema section)

### If User Says: "Improve code quality"

1. Read tasks/code-quality-debt.md
2. Pick specific issue
3. Fix issue following CONTRIBUTING.md standards
4. Run linters: `make lint`
5. Run tests: `make test`
6. Commit with descriptive message

---

## Known Issues (as of October 21, 2025)

### P0 - Critical

1. **Print statement in secure_routes.py:11**
   - File: `org_service/routes/secure_routes.py`
   - Fix: Replace with logger.info()
   - See: `tasks/p0-critical.md`

2. **Test database missing**
   - Create: `createdb org_service_test`
   - See: `tasks/p0-critical.md`

### P1 - High Priority

1. **No Pydantic schemas**
   - Need to create `schemas/` directory
   - See: `tasks/p1-high.md` task 1

2. **Hardcoded role assignment**
   - File: `auth_service.py:89`
   - Always assigns "owner" role
   - See: `tasks/p1-high.md` task 2

3. **No role enforcement**
   - Roles in JWT but no @require_role decorator
   - See: `tasks/p1-high.md` task 3

4. **Duplicate models.py at root**
   - File: `/Users/sguilfoil/Git/org-service/models.py`
   - Should be deleted
   - See: `tasks/p1-high.md` task 4

---

## Environment Setup

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Docker (optional)

### Initial Setup

1. **Create virtual environment**:
```bash
python3 -m venv venv
source venv/bin/activate
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt -r dev-requirements.txt
```

3. **Configure environment** (copy from .env.example when created):
```bash
# .env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/org_service
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-secret
GOOGLE_OAUTH_REDIRECT_URI=http://localhost:8000/auth/callback
JWT_SECRET_KEY=your-super-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRY_SECONDS=86400
```

4. **Create test database**:
```bash
createdb org_service_test
```

5. **Run migrations**:
```bash
alembic upgrade head
```

6. **Install pre-commit hooks**:
```bash
pre-commit install
```

7. **Run tests**:
```bash
pytest -v
```

---

## Make Commands

```bash
make help            # Show all commands
make install         # Install prod dependencies
make install-dev     # Install dev + prod
make dev             # Run development server
make test            # Run tests
make lint            # Run linters
make format          # Format code
make clean           # Clean caches
```

---

## When to Ask User for Clarification

**Always ask if:**
- Security implications unclear (multi-tenancy, permissions)
- Multiple valid implementation approaches
- Breaking change required
- Architectural decision needed
- User requirements ambiguous

**Examples:**
- "Should this endpoint be admin-only or accessible to all authenticated users?"
- "Should we create a new account for each user or allow users to join existing accounts?"
- "This change requires a database migration. Should I proceed?"

---

## Useful File Locations

**Code:**
- Routes: `org_service/routes/`
- Services: `org_service/services/`
- Models: `org_service/models/`
- Middleware: `org_service/middleware/`
- Schemas: `org_service/schemas/` (to be created)

**Configuration:**
- Settings: `org_service/config.py`
- Database: `org_service/db.py`
- Logging: `org_service/logging_config.py`

**Testing:**
- Test fixtures: `tests/conftest.py`
- Route tests: `tests/routes/`
- Service tests: `tests/services/` (mostly missing)

**Documentation:**
- This file: `CLAUDE.md`
- Architecture: `ARCHITECTURE.md`
- Contributing: `CONTRIBUTING.md`
- Status: `docs/implementation-status.md`
- Tasks: `tasks/`

**Migrations:**
- Alembic config: `alembic.ini`
- Migration files: `alembic/versions/`

---

## Summary Checklist for Every Task

Before starting:
- [ ] Read implementation-status.md
- [ ] Read ARCHITECTURE.md relevant sections
- [ ] Check CONTRIBUTING.md for patterns
- [ ] Review task file if exists

While coding:
- [ ] Follow layered architecture (routes → services → models)
- [ ] Add type hints to all functions
- [ ] Add Google-style docstrings
- [ ] Use logger (NOT print())
- [ ] Filter by account_id for all data queries
- [ ] Write tests (unit + integration + security)

Before finishing:
- [ ] Run tests: `pytest -v`
- [ ] Run linters: `make lint`
- [ ] Check coverage: `pytest --cov=org_service`
- [ ] Update documentation if needed
- [ ] Commit with descriptive message

---

## Questions?

If unclear on any pattern or requirement:
1. Check CONTRIBUTING.md
2. Check ARCHITECTURE.md
3. Check implementation-status.md
4. Check task files in tasks/
5. Ask user for clarification

**Remember:** This is an authentication service - security is CRITICAL. When in doubt about security, ask the user.
