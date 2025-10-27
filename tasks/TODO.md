# org-service TODO

**Phase 1 Tasks** - Things to improve for production-ready minimal auth service

---

## P0 - Critical (Do First)

### Install pytest-cov and Generate Coverage Report

**Why:** Need to measure test coverage

**Steps:**
1. Add `pytest-cov` to `dev-requirements.txt`
2. Run: `pip install pytest-cov`
3. Run: `pytest --cov=org_service --cov-report=html`
4. Open: `htmlcov/index.html`

**Target:** 80%+ coverage

**Estimate:** 30 minutes

---

## P1 - High Priority (Should Do)

### Add Pydantic Schemas for API Responses

**Why:** Type safety, better API docs, professional responses

**Current:** Returns raw dicts like `{"access_token": "...", "token_type": "bearer"}`

**With schemas:** Typed responses with validation

**Schemas needed:**
- `schemas/auth.py` - `TokenResponse`
- `schemas/user.py` - `UserContext`, `WhoAmIResponse`
- `schemas/health.py` - `HealthResponse`

**Estimate:** 1-2 hours

---

## P2 - Medium Priority (Nice to Have)

### Complete Type Hints on Route Handlers

**What:** Some routes missing return type annotations

**Example:**
```python
# Before
async def auth_callback(request: Request):
    ...

# After
async def auth_callback(request: Request) -> TokenResponse:
    ...
```

**Estimate:** 30 minutes

---

### Add pyproject.toml for Tool Configuration

**Why:** Consolidate black, ruff, mypy, pytest config into one file instead of multiple .ini files

**Estimate:** 30 minutes

---

### Add Rate Limiting to OAuth Endpoints

**Why:** Protect `/auth/login` and `/auth/callback` from spam/DoS

**Tool:** SlowAPI or similar

**Estimate:** 1-2 hours

---

## P3 - Low Priority (Future Enhancements)

### Add Request ID Middleware

**Why:** Trace requests across logs

**Estimate:** 1 hour

---

### Improve API Documentation

**Why:** Better FastAPI auto-docs with examples and descriptions

**Estimate:** 2 hours

---

### Add CI/CD Pipeline

**Why:** Automated testing and deployment

**Tool:** GitHub Actions

**Estimate:** 2-3 hours

---

### Add Structured Logging with JSON Format

**Why:** Better for log aggregation tools (CloudWatch, DataDog, etc.)

**Tool:** python-json-logger

**Estimate:** 1-2 hours

---

## Missing Features (Optional)

### Service-to-Service Authentication

**What:** Allow other microservices to validate JWTs from org-service

**Can do:** Phase 1 (no database needed)

**Estimate:** 2-3 hours

---

### Microsoft OAuth

**What:** Add Microsoft login (in addition to Google)

**Can do:** Phase 1 (no database needed)

**Estimate:** 1-2 hours

---

## Code Quality (Optional)

### Standardize Import Order

**Tool:** isort

**Estimate:** 15 minutes

---

## Summary

**P0 (Critical):** 1 task
**P1 (High):** 1 task
**P2 (Medium):** 3 tasks
**P3 (Low):** 4 tasks
**Features:** 2 tasks
**Quality:** 1 task

**Total:** 12 tasks remaining for Phase 1
