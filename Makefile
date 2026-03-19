.PHONY: help install dev test lint format check run clean
.DEFAULT_GOAL := help

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install project dependencies
	uv sync

dev: ## Install dev tools (pytest, ruff, httpx)
	uv pip install pytest pytest-asyncio httpx ruff

test: ## Run all tests
	uv run python -m pytest tests/ -v

test-astro: ## Run astro module tests only
	uv run python -m pytest tests/test_astro/ -v

lint: ## Check code with ruff
	uv run ruff check knav/ tests/

format: ## Format code with ruff
	uv run ruff format knav/ tests/

check: lint test ## Lint + test

run: ## Start FastAPI server (port 8000)
	uv run uvicorn knav.api.app:app --host 0.0.0.0 --port 8000 --reload

clean: ## Remove caches and build artifacts
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf .ruff_cache
