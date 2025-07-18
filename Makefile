.PHONY: help install install-dev venv build shell test test-container lint format clean

help:
	@echo ""
	@echo "Available targets:"
	@echo "  make install         Install prod dependencies"
	@echo "  make install-dev     Install dev + prod dependencies"
	@echo "  make venv            Create and initialize a clean virtualenv"
	@echo "  make build           Build Docker image"
	@echo "  make shell           Run interactive container with mounted code"
	@echo "  make test            Run all tests with pytest"
	@echo "  make test-container  Run tests inside Docker container"
	@echo "  make lint            Run linter (ruff)"
	@echo "  make format          Format code (black + ruff)"
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

lint:
	pre-commit run --all-files

clean:
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -exec rm -r {} +
	rm -rf .pytest_cache .ruff_cache venv
