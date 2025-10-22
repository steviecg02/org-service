# org-service Architecture

**Last Updated:** October 21, 2025

---

## Overview

org-service is a FastAPI-based microservice that handles **authentication** and **organizational identity management**. It serves as the central authentication authority for a multi-service architecture, providing:

- **OAuth-based authentication** (Google, future: Microsoft)
- **JWT token issuance and validation**
- **Multi-tenant account management**
- **Role-based access control (RBAC)**

Other microservices (sync-hostaway, sync-airbnb, etc.) depend on org-service for user authentication and authorization.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client/Browser                          │
└────────────┬────────────────────────────────────┬───────────────┘
             │                                    │
             │ 1. GET /auth/login                 │ 4. Authorization: Bearer <JWT>
             │                                    │
             v                                    v
┌─────────────────────────────────────────────────────────────────┐
│                         org-service (FastAPI)                   │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Middleware Stack                      │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │  1. SessionMiddleware (OAuth state/nonce)          │  │  │
│  │  │  2. JWTMiddleware (validate JWT, attach user)      │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐   │
│  │ Auth Routes  │  │Secure Routes │  │  Future: Admin     │   │
│  │              │  │              │  │  Routes            │   │
│  │ /auth/login  │  │/secure/whoami│  │  /admin/users      │   │
│  │ /auth/       │  │              │  │  /admin/accounts   │   │
│  │  callback    │  │              │  │                    │   │
│  └──────┬───────┘  └──────┬───────┘  └─────────┬──────────┘   │
│         │                 │                    │               │
│         v                 v                    v               │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                   Service Layer                          │  │
│  │                                                          │  │
│  │  ┌─────────────────┐       ┌──────────────────────┐     │  │
│  │  │  auth_service   │       │  Future: user_       │     │  │
│  │  │                 │       │  service, role_      │     │  │
│  │  │ - OAuth flow    │       │  service             │     │  │
│  │  │ - User creation │       │                      │     │  │
│  │  │ - JWT issuance  │       │                      │     │  │
│  │  └────────┬────────┘       └──────────────────────┘     │  │
│  └───────────┼──────────────────────────────────────────────┘  │
│              │                                                 │
│              v                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                      Models (SQLAlchemy)                 │  │
│  │                                                          │  │
│  │  ┌──────────┐  ┌──────────┐  ┌───────────────┐          │  │
│  │  │  User    │  │ Account  │  │ UserRole      │          │  │
│  │  │          │  │          │  │ (future)      │          │  │
│  │  └──────────┘  └──────────┘  └───────────────┘          │  │
│  └──────────────────────┬───────────────────────────────────┘  │
└─────────────────────────┼──────────────────────────────────────┘
                          │
                          v
           ┌──────────────────────────────┐
           │     PostgreSQL Database      │
           │                              │
           │  - users                     │
           │  - accounts                  │
           │  - user_roles (future)       │
           │  - refresh_tokens (future)   │
           └──────────────────────────────┘

                          │
                          │ 2. OAuth Redirect
                          v
           ┌──────────────────────────────┐
           │   Google OAuth Provider      │
           │                              │
           │  3. Returns: code, state     │
           └──────────────────────────────┘
```

---

## Components

### 1. Entry Point (main.py)

**Responsibilities:**
- Initialize FastAPI application
- Configure middleware stack
- Register route routers
- Define public/exempt paths

**Key Features:**
- Middleware configured in correct order
- Session middleware for OAuth state
- JWT middleware for authentication

### 2. Middleware

#### SessionMiddleware (Starlette)
- **Purpose:** Store OAuth state and nonce during login flow
- **Used by:** Google OAuth authorization flow

#### JWTMiddleware (Custom)
- **Purpose:** Validate JWT tokens on protected routes
- **File:** `org_service/middleware/jwt_middleware.py`
- **Behavior:**
  - Skip exempt paths (login, callback, docs, health)
  - Extract Authorization header
  - Decode and validate JWT
  - Attach `request.state.user` with user context
  - Return 401 if invalid/missing token
  - Log security events

**User Context Structure:**
```python
request.state.user = {
    "user_id": "uuid",
    "account_id": "uuid",
    "email": "user@example.com",
    "roles": ["owner"]
}
```

### 3. Routes

#### Auth Routes (`/auth`)
- **File:** `org_service/routes/auth_routes.py`
- **Public:** No JWT required

**Endpoints:**
- `GET /auth/login` - Redirect to Google OAuth
- `GET /auth/callback` - Handle OAuth callback, issue JWT

**Flow:**
1. User clicks "Login with Google"
2. `/auth/login` generates nonce, redirects to Google
3. Google authenticates user, redirects to `/auth/callback?code=...`
4. `/auth/callback` exchanges code for user info
5. Create/find user and account in database
6. Issue JWT with user claims
7. Return JWT to client

#### Secure Routes (`/secure`)
- **File:** `org_service/routes/secure_routes.py`
- **Protected:** JWT required

**Endpoints:**
- `GET /secure/whoami` - Returns current user info from JWT

**Future Endpoints:**
- `GET /secure/users` - List users in account
- `DELETE /secure/users/{id}` - Delete user (admin only)
- `GET /secure/account` - Get account info

### 4. Service Layer

#### auth_service.py
- **Purpose:** Business logic for authentication and user management
- **Key Functions:**

**`handle_google_callback(request, db) -> str`**
- Validates OAuth callback
- Extracts user info from Google
- Creates new account + user (first login)
- Finds existing user (subsequent logins)
- Issues JWT token

**`get_db() -> AsyncSession`**
- FastAPI dependency for database session
- Yields async SQLAlchemy session
- Auto-closes after request

**Design Principle:** All business logic lives here, not in routes. Routes are thin wrappers that call services.

### 5. Models (SQLAlchemy Core)

#### User (`models/user.py`)
```python
{
    "user_id": UUID (PK),
    "account_id": UUID (FK -> accounts),
    "email": str (unique),
    "full_name": str,
    "google_sub": str (unique, nullable),
    "password_hash": str (nullable, future),
    "created_at": datetime
}
```

#### Account (`models/account.py`)
```python
{
    "account_id": UUID (PK),
    "created_at": datetime
}
```

**Future Models:**
- `UserRole` - Many-to-many user/account/roles
- `RefreshToken` - Long-lived tokens
- `Invite` - Account invitations
- `ServiceAPIKey` - Service-to-service auth

**Note:** Using SQLAlchemy Core (not ORM) for explicit queries and better performance.

### 6. Database Layer

**Engine:** SQLAlchemy async engine with asyncpg driver
**Migrations:** Alembic
**Connection Pooling:** Built-in SQLAlchemy pool

**File:** `org_service/db.py`

```python
DATABASE_URL = "postgresql+asyncpg://user:pass@host:port/db"
engine = create_async_engine(DATABASE_URL)
async_session_maker = async_sessionmaker(bind=engine)
```

### 7. Utilities

#### JWT Utils (`utils/jwt.py`)
- `create_jwt_token(data, expiry_seconds) -> str`
- `decode_jwt_token(token) -> dict`

**JWT Structure:**
```json
{
  "sub": "user_id",
  "account_id": "account_id",
  "email": "user@example.com",
  "roles": ["owner"],
  "exp": 1234567890,
  "iat": 1234567800
}
```

**Signing:** HS256 with `JWT_SECRET_KEY` from settings

#### Logging (`logging_config.py`)
- Centralized logger configuration
- All modules import `logger` from here
- Structured logging with extra context

---

## Authentication Flow

### Google OAuth Login

```
User                Browser             org-service          Google          Database
 |                    |                      |                  |                |
 |  1. Click Login    |                      |                  |                |
 |------------------->|                      |                  |                |
 |                    |  2. GET /auth/login  |                  |                |
 |                    |--------------------->|                  |                |
 |                    |                      | 3. Generate      |                |
 |                    |                      |    nonce         |                |
 |                    |                      |                  |                |
 |                    |  4. 302 Redirect     |                  |                |
 |                    |<---------------------|                  |                |
 |                    |                      |                  |                |
 |                    |  5. GET accounts.google.com/auth        |                |
 |                    |-------------------------------------->|                |
 |                    |                      |                  |                |
 |  6. User login     |                      |                  |                |
 |<------------------------------------------------------------|                |
 |                    |                      |                  |                |
 |  7. Authorize      |                      |                  |                |
 |------------------------------------------------------------>|                |
 |                    |                      |                  |                |
 |                    |  8. 302 /auth/callback?code=xxx         |                |
 |                    |<--------------------------------------|                |
 |                    |                      |                  |                |
 |                    |  9. GET /auth/callback?code=xxx        |                |
 |                    |--------------------->|                  |                |
 |                    |                      | 10. Exchange code|                |
 |                    |                      |    for token     |                |
 |                    |                      |----------------->|                |
 |                    |                      | 11. User info    |                |
 |                    |                      |<-----------------|                |
 |                    |                      |                  |                |
 |                    |                      | 12. Find/create  |                |
 |                    |                      |     user         |                |
 |                    |                      |-------------------------------->|
 |                    |                      | 13. User record  |                |
 |                    |                      |<--------------------------------|
 |                    |                      |                  |                |
 |                    |                      | 14. Generate JWT |                |
 |                    |                      |                  |                |
 |                    | 15. {access_token}   |                  |                |
 |                    |<---------------------|                  |                |
 |  16. Store JWT     |                      |                  |                |
 |<-------------------|                      |                  |                |
```

### Protected API Access

```
Client              org-service              Database
  |                      |                       |
  |  1. GET /secure/whoami                      |
  |     Authorization: Bearer <JWT>             |
  |--------------------->|                       |
  |                      |                       |
  |                      | 2. JWTMiddleware:     |
  |                      |    - Extract token    |
  |                      |    - Validate sig     |
  |                      |    - Check expiry     |
  |                      |                       |
  |                      | 3. Attach user to     |
  |                      |    request.state      |
  |                      |                       |
  |                      | 4. Route handler:     |
  |                      |    - Access user      |
  |                      |    - Return data      |
  |                      |                       |
  |  5. {user: {...}}    |                       |
  |<---------------------|                       |
```

---

## Security Model

### Multi-Tenancy

**Principle:** Every user belongs to exactly one account. All data queries MUST filter by `account_id`.

**Implementation:**
1. JWT contains `account_id` claim
2. Middleware attaches `account_id` to `request.state.user`
3. All database queries filter by `account_id`

**Example:**
```python
# routes/user_routes.py
async def list_users(request: Request, db: AsyncSession):
    account_id = request.state.user["account_id"]

    # CRITICAL: Filter by account_id
    result = await db.execute(
        select(User).where(User.account_id == account_id)
    )
    return result.scalars().all()
```

**⚠️ Security Rule:** NEVER query users, accounts, or account-scoped data without filtering by `account_id`.

### Role-Based Access Control (RBAC)

**Current Status:** JWT contains roles, but enforcement not yet implemented

**Design:**
- Roles are account-scoped (not global)
- User can have multiple roles within an account
- Roles stored in `user_roles` table (to be created)

**Standard Roles:**
- `owner` - Full account admin (first user in account)
- `admin` - Can manage users, settings
- `member` - Standard user access

**Enforcement (to be implemented):**
```python
@require_role(["admin", "owner"])
async def delete_user(user_id: str, request: Request):
    ...
```

### JWT Security

**Token Lifecycle:**
1. **Issuance:** After successful OAuth callback
2. **Storage:** Client stores in localStorage/sessionStorage
3. **Usage:** Sent in `Authorization: Bearer <token>` header
4. **Validation:** Every request (via JWTMiddleware)
5. **Expiration:** Configurable (default: 24 hours)

**Security Features:**
- Signed with HS256 algorithm
- Secret key from environment (JWT_SECRET_KEY)
- Expiry check on every validation
- Logged failures for security monitoring

**Future Enhancements:**
- Refresh tokens for long-lived sessions
- Token revocation
- Shorter expiry (1 hour) with refresh mechanism

---

## Database Schema

### Current Schema

```sql
-- accounts table
CREATE TABLE accounts (
    account_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMP DEFAULT NOW()
);

-- users table
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL REFERENCES accounts(account_id),
    email VARCHAR UNIQUE NOT NULL,
    full_name VARCHAR NOT NULL,
    google_sub VARCHAR UNIQUE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_users_account_id ON users(account_id);
CREATE INDEX idx_users_email ON users(email);
```

### Future Schema

```sql
-- user_roles table (many-to-many)
CREATE TABLE user_roles (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(user_id),
    account_id UUID REFERENCES accounts(account_id),
    role_name VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, account_id, role_name)
);

-- refresh_tokens table
CREATE TABLE refresh_tokens (
    token_id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(user_id),
    account_id UUID REFERENCES accounts(account_id),
    token_hash VARCHAR UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    is_revoked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- invites table
CREATE TABLE invites (
    invite_id UUID PRIMARY KEY,
    account_id UUID REFERENCES accounts(account_id),
    invited_email VARCHAR NOT NULL,
    invited_by_user_id UUID REFERENCES users(user_id),
    invite_token VARCHAR UNIQUE NOT NULL,
    role_name VARCHAR DEFAULT 'member',
    expires_at TIMESTAMP NOT NULL,
    accepted_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## Configuration

### Environment Variables

**Required:**
- `DATABASE_URL` - PostgreSQL connection string
- `GOOGLE_CLIENT_ID` - Google OAuth client ID
- `GOOGLE_CLIENT_SECRET` - Google OAuth secret
- `GOOGLE_OAUTH_REDIRECT_URI` - OAuth callback URL
- `JWT_SECRET_KEY` - Secret for signing JWTs
- `JWT_ALGORITHM` - JWT algorithm (default: HS256)
- `JWT_EXPIRY_SECONDS` - Token expiry (default: 86400)

**Configuration File:** `org_service/config.py`

Uses Pydantic `BaseSettings` for type-safe config loading from environment.

---

## Key Design Decisions

### 1. SQLAlchemy Core (Not ORM)

**Reason:**
- More explicit and predictable queries
- Better performance (no lazy loading issues)
- Easier to audit for security (multi-tenancy)
- More control over SQL execution

**Trade-off:** More verbose than ORM, but worth it for production services handling authentication.

### 2. Alembic for All Migrations

**Reason:**
- Version-controlled schema changes
- Rollback capability
- Production-safe migrations
- No programmatic table creation

**Pattern:** NEVER use `Base.metadata.create_all()` in code

### 3. Thin Routes, Fat Services

**Reason:**
- Easier to test business logic (mock database, not FastAPI)
- Routes focus on HTTP concerns (params, responses, errors)
- Services focus on business rules
- Cleaner separation of concerns

**Pattern:**
```python
# Route handler (thin)
@router.post("/users")
async def create_user(user_data: UserCreate, db = Depends(get_db)):
    user = await auth_service.create_user(user_data, db)
    return user

# Service (fat - business logic)
async def create_user(user_data: UserCreate, db: AsyncSession):
    # Validation
    # Business rules
    # Database operations
    # Return result
```

### 4. JWT in Authorization Header (Not Cookies)

**Reason:**
- Works with CORS for API access
- Client has full control over token
- Easier for mobile apps
- Standard pattern for API authentication

**Trade-off:** Client must manage token storage and refresh

### 5. Multi-Tenancy via account_id

**Reason:**
- Shared database, isolated data
- Simpler than separate databases per tenant
- Easier to manage and backup
- Scales well for moderate number of accounts

**Critical Requirement:** EVERY query must filter by account_id

---

## Future Architecture Considerations

### 1. Service-to-Service Communication

Other microservices will need to:
- Validate JWTs issued by org-service
- Query user information
- Check permissions

**Options:**
- **Option A:** Service API keys + internal endpoints
- **Option B:** JWT validation library shared across services
- **Option C:** org-service as auth gateway (reverse proxy)

**Recommended:** Option A (service API keys) - see `tasks/missing-features.md`

### 2. Caching

**Candidates for Caching:**
- JWT validation (cache decoded tokens for 1 minute)
- User roles (cache per user_id + account_id)
- Account settings (future)

**Technology:** Redis

### 3. Observability

**Metrics to Track:**
- Login success/failure rate
- JWT validation failures
- OAuth callback errors
- API response times

**Tools:** Prometheus + Grafana or DataDog

### 4. Rate Limiting

**Critical Endpoints:**
- `/auth/login` - Prevent OAuth spam
- `/auth/callback` - Prevent brute force
- `/auth/refresh` (future) - Prevent token farming

**Tool:** SlowAPI or nginx rate limiting

---

## Testing Strategy

### Unit Tests
- **Target:** Service layer, utilities
- **Mocks:** Database, OAuth provider
- **Examples:**
  - `test_create_jwt_token_includes_expiry()`
  - `test_handle_google_callback_with_incomplete_userinfo()`

### Integration Tests
- **Target:** Route handlers
- **Real:** Database (test DB), middleware
- **Mocked:** External APIs (Google OAuth)
- **Examples:**
  - `test_callback_creates_user_if_not_exists()`
  - `test_whoami_requires_valid_jwt()`

### Security Tests
- **Target:** Multi-tenancy, authentication, authorization
- **Examples:**
  - `test_user_cannot_access_other_account_data()`
  - `test_expired_jwt_returns_401()`
  - `test_delete_user_requires_admin_role()`

**Coverage Target:** 80% overall, 90% for core modules

---

## Deployment

### Docker

**Dockerfile:** Multi-stage build
- Base: Python 3.11-slim
- Install system dependencies (gcc, libpq-dev)
- Install Python dependencies
- Copy application code

**docker-compose.yml:** Local development
- PostgreSQL service (TimescaleDB)
- org-service with hot reload

### Production Checklist

- [ ] Environment variables from secrets manager
- [ ] Database migrations applied
- [ ] Health check endpoint monitoring
- [ ] Structured JSON logging enabled
- [ ] Rate limiting configured
- [ ] CORS configured for production domains
- [ ] TLS/HTTPS enforced
- [ ] Database backups configured

---

## References

- **FastAPI Documentation:** https://fastapi.tiangolo.com/
- **SQLAlchemy Core:** https://docs.sqlalchemy.org/en/20/core/
- **Alembic:** https://alembic.sqlalchemy.org/
- **Authlib:** https://docs.authlib.org/
- **Security Patterns:** See `SECURITY-PATTERNS.md` in repository root

---

## Appendix: File Structure

```
org_service/
├── main.py                      # FastAPI app, middleware, routing
├── config.py                    # Pydantic settings
├── db.py                        # Database engine
├── logging_config.py            # Logging setup
│
├── routes/
│   ├── auth_routes.py           # OAuth login/callback
│   └── secure_routes.py         # Protected endpoints
│
├── middleware/
│   └── jwt_middleware.py        # JWT validation
│
├── services/
│   └── auth_service.py          # Business logic
│
├── models/
│   ├── base.py                  # SQLAlchemy Base
│   ├── user.py                  # User table
│   └── account.py               # Account table
│
├── schemas/                     # TODO: Pydantic models
│   ├── user.py
│   └── account.py
│
├── utils/
│   └── jwt.py                   # JWT utilities
│
└── devtools/                    # Development utilities

tests/
├── conftest.py                  # Shared fixtures
├── routes/                      # Route tests
├── middleware/                  # Middleware tests
└── utils/                       # Utility tests

alembic/
├── versions/                    # Migration files
└── env.py                       # Alembic config

docs/
└── implementation-status.md     # Audit report

tasks/
├── p0-critical.md               # Critical tasks
├── p1-high.md                   # High priority
├── p2-medium.md                 # Medium priority
├── p3-low.md                    # Low priority
├── missing-features.md          # Feature backlog
└── code-quality-debt.md         # Tech debt

CONTRIBUTING.md                  # Developer guide
ARCHITECTURE.md                  # This file
CLAUDE.md                        # AI assistant guide (future)
README.md                        # Project overview
```
