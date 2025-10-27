# Code Standards Enforcement

**Purpose:** Automated enforcement of code standards. Developers can't merge code that violates standards.

**Strategy:** Prevention (pre-commit) + Validation (CI/CD) + Education (documentation)

---

## 1. Pre-Commit Hooks (Local Enforcement)

**Install once per repo, runs automatically on every commit.**

### `.pre-commit-config.yaml`

```yaml
repos:
  # Code formatting (auto-fix)
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.6
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format

  # Type checking (fail if types missing)
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.1
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
        args: [--strict, --ignore-missing-imports]

  # Security checks
  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.5
    hooks:
      - id: bandit
        args: [-c, pyproject.toml]

  # Secrets detection
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']

  # Fast unit tests (< 5 seconds)
  - repo: local
    hooks:
      - id: pytest-fast
        name: pytest (fast unit tests)
        entry: pytest
        args: [-m, unit, --maxfail=1, --tb=short]
        language: system
        pass_filenames: false
        always_run: true
```

### Setup Instructions

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually on all files (first time)
pre-commit run --all-files

# Create secrets baseline (first time)
detect-secrets scan > .secrets.baseline
```

### What Gets Blocked

❌ **Commit will FAIL if:**
- Code isn't formatted (ruff)
- Type hints missing (mypy --strict)
- Complexity > 10 (ruff)
- Security issues found (bandit)
- Secrets detected (detect-secrets)
- Fast unit tests fail (pytest -m unit)

✅ **Auto-fixed if possible:**
- Code formatting
- Import sorting
- Trailing whitespace

---

## 2. Ruff Configuration (pyproject.toml)

**Enforces complexity, line length, code quality.**

### `pyproject.toml`

```toml
[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = [
    "E",      # pycodestyle errors
    "W",      # pycodestyle warnings
    "F",      # pyflakes
    "I",      # isort
    "N",      # pep8-naming
    "UP",     # pyupgrade
    "B",      # flake8-bugbear
    "C4",     # flake8-comprehensions
    "C90",    # mccabe complexity
    "DTZ",    # flake8-datetimez
    "T10",    # flake8-debugger
    "EM",     # flake8-errmsg
    "EXE",    # flake8-executable
    "ISC",    # flake8-implicit-str-concat
    "PIE",    # flake8-pie
    "PT",     # flake8-pytest-style
    "Q",      # flake8-quotes
    "RET",    # flake8-return
    "SIM",    # flake8-simplify
    "TID",    # flake8-tidy-imports
    "ARG",    # flake8-unused-arguments
    "PTH",    # flake8-use-pathlib
    "ERA",    # eradicate (commented-out code)
    "PL",     # pylint
    "TRY",    # tryceratops
    "RUF",    # ruff-specific rules
]

ignore = [
    "E501",   # line too long (handled by formatter)
    "PLR0913", # too many arguments (sometimes needed)
]

[tool.ruff.lint.mccabe]
max-complexity = 10  # Functions must be < 10 complexity

[tool.ruff.lint.per-file-ignores]
"__init__.py" = ["F401"]  # Allow unused imports in __init__
"tests/*" = ["ARG", "PLR2004"]  # Allow magic values in tests

[tool.ruff.lint.pylint]
max-args = 6
max-branches = 12
max-returns = 6
max-statements = 50
```

---

## 3. Mypy Configuration (Type Checking)

**Enforces type hints on all functions.**

### `pyproject.toml` (add to above file)

```toml
[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = false  # Allow @retry, @app.get, etc.
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
strict_equality = true

# Per-module ignores for third-party libraries
[[tool.mypy.overrides]]
module = [
    "tenacity.*",
    "pybreaker.*",
    "prometheus_client.*",
]
ignore_missing_imports = true
```

---

## 4. Pytest Configuration (Testing)

**Enforces test coverage thresholds.**

### `pyproject.toml` (add to above file)

```toml
[tool.pytest.ini_options]
minversion = "7.0"
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]

# Markers for test organization
markers = [
    "unit: Fast unit tests (< 100ms each)",
    "integration: Integration tests (real DB, mocked APIs)",
    "e2e: End-to-end tests (full workflow)",
    "slow: Slow tests (> 1 second)",
]

# Coverage configuration
addopts = [
    "--strict-markers",
    "--strict-config",
    "-ra",                              # Show summary of all test outcomes
    "--cov=src",                        # Coverage for src directory
    "--cov-report=term-missing",        # Show missing lines
    "--cov-report=html",                # HTML report
    "--cov-fail-under=80",              # Fail if < 80% coverage
]

[tool.coverage.run]
source = ["src"]
omit = [
    "*/tests/*",
    "*/migrations/*",
    "*/__init__.py",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
    "@abstractmethod",
]

# Fail if coverage below threshold
fail_under = 80

# Per-module coverage requirements
[tool.coverage.paths]
source = ["src"]

# Specific modules need higher coverage
[[tool.coverage.report.precision]]
services = 90
models = 90
```

---

## 5. CI/CD Pipeline (GitHub Actions)

**Runs on every PR, blocks merge if standards violated.**

### `.github/workflows/ci.yml`

```yaml
name: CI

on:
  pull_request:
    branches: [main, develop]
  push:
    branches: [main]

jobs:
  quality:
    name: Code Quality Checks
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r dev-requirements.txt

      - name: Run ruff (linting)
        run: ruff check .

      - name: Run ruff format (check formatting)
        run: ruff format --check .

      - name: Run mypy (type checking)
        run: mypy src/

      - name: Run bandit (security)
        run: bandit -r src/ -c pyproject.toml

      - name: Check for secrets
        run: |
          pip install detect-secrets
          detect-secrets scan --baseline .secrets.baseline

  test:
    name: Tests
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r dev-requirements.txt

      - name: Run unit tests
        run: pytest -m unit -v

      - name: Run integration tests
        run: pytest -m integration -v
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test

      - name: Check coverage
        run: pytest --cov --cov-fail-under=80

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
          fail_ci_if_error: true

  security:
    name: Security Scan
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          format: 'sarif'
          output: 'trivy-results.sarif'

      - name: Upload Trivy results to GitHub Security
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-results.sarif'
```

---

## 6. Branch Protection Rules (GitHub Settings)

**Configure in GitHub repo settings → Branches → Add rule for `main`**

Required settings:
- ✅ Require pull request reviews before merging
- ✅ Require status checks to pass before merging
  - `quality / Code Quality Checks`
  - `test / Tests`
  - `security / Security Scan`
- ✅ Require branches to be up to date before merging
- ✅ Require conversation resolution before merging
- ❌ Do not allow bypassing the above settings

---

## 7. Makefile (Developer Convenience)

**Easy commands to run checks locally.**

### `Makefile`

```makefile
.PHONY: help install format lint typecheck test test-fast test-cov check clean

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install dependencies
	pip install -r requirements.txt
	pip install -r dev-requirements.txt
	pre-commit install

format:  ## Format code
	ruff format .
	ruff check --fix .

lint:  ## Run linter
	ruff check .

typecheck:  ## Run type checker
	mypy src/

test-fast:  ## Run fast unit tests
	pytest -m unit -v

test:  ## Run all tests
	pytest -v

test-cov:  ## Run tests with coverage report
	pytest --cov --cov-report=html --cov-report=term-missing
	@echo "Open htmlcov/index.html to see coverage report"

security:  ## Run security checks
	bandit -r src/ -c pyproject.toml
	detect-secrets scan --baseline .secrets.baseline

check: format lint typecheck test-cov security  ## Run all checks (same as CI)

clean:  ## Clean up cache and temp files
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage
```

---

## 8. How to Apply to Existing Repo

### Step 1: Copy Configuration Files

```bash
cd your-repo

# Copy files from control-room/resources/
cp /path/to/control-room/resources/CODE-STANDARDS.md .
cp /path/to/control-room/resources/ENFORCEMENT.md .

# Create configuration files
touch pyproject.toml Makefile .pre-commit-config.yaml
```

### Step 2: Install Tools

```bash
# Create dev-requirements.txt
cat > dev-requirements.txt << EOF
ruff>=0.1.6
mypy>=1.7
pytest>=7.4
pytest-cov>=4.1
pytest-asyncio>=0.21
pre-commit>=3.5
bandit>=1.7
detect-secrets>=1.4
structlog>=23.2
tenacity>=8.2
pybreaker>=1.0
prometheus-client>=0.19
EOF

# Install
pip install -r dev-requirements.txt

# Setup pre-commit
pre-commit install
```

### Step 3: Create Baseline (Ignore Existing Issues)

```bash
# Run checks to see current state
make check

# Generate baseline for secrets
detect-secrets scan > .secrets.baseline

# Generate baseline for security issues (if needed)
bandit -r src/ -f json -o .bandit-baseline.json

# Fix auto-fixable issues
make format
```

### Step 4: Gradual Adoption

**Option A: All at once (small repos)**
```bash
# Fix all issues
make format
make lint
make typecheck
# Fix remaining issues manually
make check  # Should pass
```

**Option B: Gradual (large repos)**

Add to `pyproject.toml`:
```toml
[tool.ruff.lint.per-file-ignores]
# Ignore existing files (remove as you fix them)
"src/old_module.py" = ["ALL"]
"src/legacy/*" = ["ALL"]
```

Then fix files incrementally, removing from ignore list.

### Step 5: Enable CI/CD

```bash
# Create GitHub Actions workflow
mkdir -p .github/workflows
cp /path/to/ci.yml .github/workflows/

# Commit and push
git add .
git commit -m "chore: Add code standards enforcement"
git push
```

### Step 6: Configure Branch Protection

1. Go to GitHub repo → Settings → Branches
2. Add rule for `main` branch
3. Enable all required checks (see section 6 above)

---

## 9. Enforcement Levels

### Level 1: Pre-commit (Developer Machine)
- Runs on every `git commit`
- Fast checks only (< 10 seconds)
- Auto-fixes when possible
- **Blocks commit** if critical issues found

### Level 2: CI/CD (GitHub Actions)
- Runs on every PR
- Full checks (linting, type checking, all tests, security)
- Takes 2-5 minutes
- **Blocks merge** if any check fails

### Level 3: Branch Protection (GitHub Settings)
- Requires CI/CD to pass
- Requires code review
- Requires conflicts resolved
- **Cannot bypass** (even admins)

---

## 10. Developer Workflow

```bash
# Start feature
git checkout -b feature/new-feature

# Write code...
# Write tests...

# Run checks locally
make check

# Commit (pre-commit hooks run automatically)
git commit -m "feat: Add new feature"

# Push (CI/CD runs automatically)
git push origin feature/new-feature

# Create PR (branch protection enforces checks)
# Get review, merge to main
```

---

## Summary

**Prevention** (pre-commit) + **Validation** (CI/CD) + **Enforcement** (branch protection) = **Standards that stick**

Nobody can merge code that violates standards. It's automated, not optional.
