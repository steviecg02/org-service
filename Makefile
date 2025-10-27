.PHONY: help install install-dev venv build shell test test-cov test-container lint format typecheck security check clean

help:
	@echo ""
	@echo "Available targets:"
	@echo "  make install         Install prod dependencies"
	@echo "  make install-dev     Install dev + prod dependencies"
	@echo "  make venv            Create and initialize a clean virtualenv"
	@echo "  make build           Build Docker image"
	@echo "  make shell           Run interactive container with mounted code"
	@echo "  make test            Run all tests with pytest"
	@echo "  make test-cov        Run tests with coverage report"
	@echo "  make test-container  Run tests inside Docker container"
	@echo "  make lint            Run pre-commit hooks (ruff, mypy, tests)"
	@echo "  make format          Format code with ruff"
	@echo "  make typecheck       Run mypy type checker"
	@echo "  make security        Run bandit security checks"
	@echo "  make check           Run all checks (format, lint, typecheck, test-cov, security)"
	@echo "  make clean           Remove __pycache__ and .pyc files"
	@echo ""

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt -r dev-requirements.txt

venv:
	python3 -m venv venv && source venv/bin/activate && make install-dev

dev:
	PYTHONPATH=. uvicorn org_service.main:app --reload

build:
	docker build -t org-service .

shell:
	docker run -it --rm \
		--env-file=.env \
		-v $(PWD):/app \
		-w /app \
		org-service \
		/bin/bash

test-container:
	docker run --rm \
		--env-file=.env \
		-v $(PWD):/app \
		-w /app \
		org-service \
		make test

test:
	PYTHONPATH=. pytest -v --tb=short

test-cov:
	PYTHONPATH=. pytest --cov --cov-report=html --cov-report=term-missing
	@echo "Open htmlcov/index.html to see coverage report"

format:
	ruff format .
	ruff check --fix .

typecheck:
	mypy org_service/

security:
	bandit -c pyproject.toml -r org_service/
	detect-secrets scan --baseline .secrets.baseline

lint:
	pre-commit run --all-files

check: format lint test-cov security
	@echo "All checks passed!"

clean:
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -exec rm -r {} +
	rm -rf .mypy_cache .pytest_cache .ruff_cache htmlcov .coverage venv
