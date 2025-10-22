# P0 - Critical Security Tasks

**Priority:** IMMEDIATE - Fix before any production deployment

**Estimated Time:** 2-4 hours

---

## 1. Remove print() Statement from Production Code

**File:** `org_service/routes/secure_routes.py:11`

**Issue:**
```python
# Current (WRONG)
print("👤 request.state.user:", request.state.user)
```

**Security Risk:**
- Leaks sensitive user data (user_id, account_id, email, roles) to stdout
- Bypasses logging controls
- Data may appear in container logs without proper redaction

**Fix:**
```python
# Replace with structured logging
from org_service.logging_config import logger

logger.info(
    "User accessed whoami endpoint",
    extra={
        "user_id": request.state.user["user_id"],
        "account_id": request.state.user["account_id"]
    }
)
```

**Steps:**
1. Import logger at top of file
2. Replace print() with logger.info()
3. Use structured logging (extra dict)
4. Do NOT log full user dict (includes email, which is PII)
5. Run tests to verify functionality unchanged
6. Commit with message: "fix(security): remove print statement from secure routes"

---

## 2. Create Test Database and Verify Tests Pass

**Issue:** Test database doesn't exist - all tests failing

**Steps:**
1. Create test database:
   ```bash
   createdb org_service_test
   ```

2. Run Alembic migrations on test DB:
   ```bash
   # Temporarily set DATABASE_URL to test DB
   DATABASE_URL=postgresql://postgres:postgres@localhost:5432/org_service_test alembic upgrade head
   ```

3. Run tests:
   ```bash
   source venv/bin/activate
   pytest -v
   ```

4. Verify all 12 tests pass

5. If any tests fail:
   - Investigate failure
   - Fix test or code
   - Re-run until all pass

**Expected Output:**
```
============================== 12 passed in X.XXs ===============================
```

---

## 3. Install pytest-cov and Generate Coverage Report

**Issue:** Cannot measure test coverage (pytest-cov missing)

**Steps:**
1. Add to dev-requirements.txt:
   ```
   pytest-cov
   ```

2. Install in venv:
   ```bash
   source venv/bin/activate
   pip install pytest-cov
   ```

3. Run coverage:
   ```bash
   pytest --cov=org_service --cov-report=term --cov-report=html
   ```

4. Review coverage report:
   ```bash
   open htmlcov/index.html
   ```

5. Document coverage % in implementation-status.md:
   - Update "Coverage Report" section with actual %
   - Identify modules with <80% coverage

6. Commit dev-requirements.txt change:
   ```bash
   git add dev-requirements.txt
   git commit -m "chore: add pytest-cov to dev dependencies"
   ```

**Target:** 80%+ overall coverage

---

## Acceptance Criteria

- [ ] No print() statements in org_service/ directory
- [ ] Test database exists and migrations applied
- [ ] All 12 tests passing
- [ ] pytest-cov installed
- [ ] Coverage report generated
- [ ] Coverage documented in implementation-status.md
- [ ] All changes committed to git

---

## Next Steps After P0

Once all P0 tasks complete, move to P1 tasks in `tasks/p1-high.md`.
