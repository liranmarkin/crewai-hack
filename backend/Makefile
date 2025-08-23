.PHONY: install install-dev format lint type-check test clean run

install:
	pip install -r requirements.txt

install-dev: install
	pip install -r requirements-dev.txt

format:
	black .
	ruff check --fix .

lint:
	ruff check .
	black --check .

type-check:
	mypy .

test:
	pytest

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true

run:
	uvicorn main:app --reload --port 8000

check: lint type-check