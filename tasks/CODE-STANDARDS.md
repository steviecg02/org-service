# Python Code Standards (Quick Reference)

**Purpose:** Production-grade Python standards for all repositories. This is the TL;DR version - detailed examples in GENERIC-REPO-SETUP-TEMPLATE.md.

---

## ✅ Code Quality Checklist (PR Requirements)

Before merging ANY pull request, verify:

- [ ] **Type hints** on all functions (use `from __future__ import annotations`)
- [ ] **Docstrings** (Google style) on all public functions/classes
- [ ] **Tests written** (80% coverage minimum, 90% for business logic)
- [ ] **No bare `except:` clauses** - catch specific exceptions
- [ ] **Structured logging** (no `print()` statements)
- [ ] **Functions < 50 lines, complexity < 10**
- [ ] **No hardcoded secrets** - use environment variables
- [ ] **Input validation** - use Pydantic or similar
- [ ] **Pre-commit hooks pass** (ruff, mypy, pytest)

---

## 🏗️ Architecture Patterns (Non-Negotiable)

### Separation of Concerns
```
✅ client.py or api/     - External API calls
✅ db/ or database.py    - Database operations
✅ services/             - Business logic
✅ models/               - Data models
✅ utils/                - Pure utilities

❌ NEVER mix database logic with API calls in the same function
```

### Dependency Injection
```python
# ✅ CORRECT
def save_user(engine: Engine, user: dict) -> None:
    with engine.begin() as conn:
        conn.execute(...)

# ❌ WRONG
def save_user(user: dict) -> None:
    global_engine.execute(...)  # Avoid globals
```

---

## 🧪 Testing (What to Test)

**Priority Order:**
1. **Business logic** - Calculations, validation (90%+ coverage)
2. **Error handling** - What happens when things fail?
3. **Integration points** - DB/API interactions
4. **Edge cases** - Empty inputs, null values

**Rules:**
- Test **behaviors**, not implementation details
- Test happy path AND error cases
- Never merge to main without tests

---

## ⚡ Production Reliability (Required Patterns)

### External API Calls - MUST Have Retries
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
def call_external_api(url: str) -> dict:
    response = requests.get(url, timeout=5)
    response.raise_for_status()
    return response.json()
```

### Database Connections - MUST Have Pooling
```python
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,      # Test connection before use
    pool_recycle=3600        # Recycle after 1 hour
)
```

### Services - MUST Have Health Checks
```python
@app.get("/health")
async def health_check():
    # Check database, external APIs, etc.
    return {"status": "healthy"}
```

### Services - MUST Handle Graceful Shutdown
```python
import signal

def shutdown_handler(signum, frame):
    logger.info("Shutdown signal received")
    engine.dispose()  # Close connections
    sys.exit(0)

signal.signal(signal.SIGTERM, shutdown_handler)
```

---

## 🔐 Security (Critical Requirements)

### Never Hardcode Secrets
```python
# ❌ NEVER
API_KEY = "sk_live_abc123"

# ✅ ALWAYS
API_KEY = os.environ["API_KEY"]

# ✅ PRODUCTION
API_KEY = get_secret("api-key")  # Secret manager
```

### Always Validate Inputs
```python
from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    password: constr(min_length=8)

# Pydantic validates automatically
def create_user(data: UserCreate) -> User:
    ...
```

### Never Use String Formatting for SQL
```python
# ❌ SQL INJECTION
query = f"SELECT * FROM users WHERE id = {user_id}"

# ✅ PARAMETERIZED
query = text("SELECT * FROM users WHERE id = :user_id")
conn.execute(query, {"user_id": user_id})
```

---

## 📊 Observability (Production Requirements)

### Structured Logging
```python
import structlog

logger = structlog.get_logger()

logger.info(
    "user_created",
    user_id=user.id,
    org_id=org.id
)
```

### Metrics
```python
from prometheus_client import Counter, Histogram

requests_total = Counter('api_requests_total', 'Total requests', ['endpoint', 'status'])
request_duration = Histogram('api_request_duration_seconds', 'Request duration', ['endpoint'])

# Track in code
requests_total.labels(endpoint='/users', status='success').inc()
```

---

## 🛡️ Error Handling Pattern

```python
import logging

logger = logging.getLogger(__name__)

try:
    result = risky_operation()
except requests.Timeout as e:
    logger.error("operation_timeout", extra={"error": str(e)})
    raise
except ValueError as e:
    logger.warning("invalid_input", extra={"error": str(e)})
    return None
except Exception as e:
    logger.error("unexpected_error", extra={"error": str(e)}, exc_info=True)
    raise

# ❌ NEVER do this
except:
    pass
```

---

## 📏 Code Quality Metrics

- **Cyclomatic complexity:** < 10 (ruff checks this)
- **Function length:** < 50 lines
- **Nesting depth:** < 3 levels (use early returns)
- **Test coverage:** 80% overall, 90% business logic
- **Type hint coverage:** 100%
- **Docstring coverage:** 100% public functions

---

## 🔧 Enforcement Tools

See [ENFORCEMENT.md](ENFORCEMENT.md) for pre-commit hooks, CI/CD pipeline configuration, and automated enforcement.

---

## 📚 Detailed Examples

For detailed examples and full audit process, see [GENERIC-REPO-SETUP-TEMPLATE.md](GENERIC-REPO-SETUP-TEMPLATE.md).
