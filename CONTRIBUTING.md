# Contributing to org-service

**Phase 1: Minimal Implementation** - Keep it simple!

---

## Code Style

### Python Standards

- **Python 3.11+** required
- **Black** for formatting (line length: 88)
- **Ruff** for linting
- **Type hints** on all functions
- **Docstrings** on all public functions (Google style)

### Run Formatters

```bash
# Format code
black org_service/ tests/

# Lint code
ruff check org_service/ tests/

# Type check
mypy org_service/
```

### Pre-commit Hooks

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

---

## Project Structure

```
org_service/
├── main.py              # FastAPI app + health check
├── config.py            # Settings (env vars)
├── routes/              # API endpoints
├── services/            # Business logic (OAuth handling)
├── middleware/          # JWT validation
└── utils/               # JWT encode/decode
```

**Keep it simple** - No database, no complex architecture.

---

## Architecture Patterns

### 1. Routes are Thin

Routes should ONLY:
- Extract request parameters
- Call service functions
- Return responses

```python
# ✅ GOOD
@router.get("/callback")
async def auth_callback(request: Request):
    jwt_token = await handle_google_callback(request)
    return {"access_token": jwt_token, "token_type": "bearer"}

# ❌ BAD - Business logic in route
@router.get("/callback")
async def auth_callback(request: Request):
    token = await oauth.google.authorize_access_token(request)
    userinfo = await oauth.google.parse_id_token(token, nonce)
    # ... more logic here
```

### 2. Services Contain Business Logic

All OAuth handling, validation, JWT generation goes in `services/`.

### 3. No Database

Phase 1 has NO database. Don't add one.

---

## Testing

### Run Tests

```bash
pytest -v
pytest --cov=org_service --cov-report=html
```

### Write Tests

- Test files in `tests/` mirror `org_service/` structure
- Use fixtures from `conftest.py`
- Mock OAuth responses with `mock_oauth` fixture

```python
@pytest.mark.asyncio
async def test_callback_returns_jwt(async_client, mock_oauth):
    mock_oauth.google.parse_id_token.return_value = {
        "sub": "google-123",
        "email": "test@example.com",
        "name": "Test User",
    }

    response = await async_client.get("/auth/callback?code=fake")
    assert response.status_code == 200
    assert "access_token" in response.json()
```

---

## Adding Features

### Before Adding Anything

**Ask:** Does this belong in Phase 1?

Phase 1 is **minimal**. Features that require database, user management, role enforcement → wait for Phase 2.

### What You CAN Add

- ✅ Additional OAuth providers (Microsoft, GitHub)
- ✅ More JWT claims (if needed by other services)
- ✅ Better error handling
- ✅ More logging
- ✅ CORS configuration
- ✅ Rate limiting

### What to AVOID

- ❌ Database / SQLAlchemy
- ❌ User storage
- ❌ Account management
- ❌ Complex role systems
- ❌ Invite systems
- ❌ Multi-tenancy (Phase 1 uses hardcoded org_id)

---

## Environment Variables

Required in `.env`:

```env
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_OAUTH_REDIRECT_URI=http://localhost:8000/auth/callback
JWT_SECRET_KEY=...  # openssl rand -hex 32
```

Optional (have defaults):

```env
JWT_ALGORITHM=HS256
JWT_EXPIRY_SECONDS=604800  # 7 days
HARDCODED_ORG_ID=11111111-1111-1111-1111-111111111111
```

---

## Pull Requests

1. **Create a branch** from `main`
2. **Make your changes** following code style
3. **Add tests** for new functionality
4. **Run formatters and tests**
   ```bash
   black org_service/ tests/
   ruff check org_service/ tests/
   pytest -v
   ```
5. **Update README** if adding user-facing features
6. **Submit PR** with clear description

---

## Common Pitfalls

### ❌ Using `print()` for logging

```python
# BAD
print("User logged in:", email)

# GOOD
from org_service.logging_config import logger
logger.info("User logged in", extra={"email": email})
```

### ❌ Importing deleted modules

If you see errors like:
- `ModuleNotFoundError: No module named 'org_service.models'`
- `ModuleNotFoundError: No module named 'org_service.db'`

These modules were **deleted in Phase 1**. Don't try to add them back.

### ❌ Adding database migrations

Phase 1 has **no database**. Alembic was removed.

---

## Questions?

- Check [README.md](README.md) for setup instructions
- See `docs/archive/` for old Phase 2 planning docs
- Open an issue for clarification

---

## Phase 2 Planning

When we need database/multi-tenancy:
- See `docs/archive/ARCHITECTURE.md` for original design
- See `docs/archive/tasks/` for feature backlog
- That's when we add PostgreSQL, Alembic, user storage, etc.

**But not now.** Keep Phase 1 simple.
