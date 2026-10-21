# Development commands. Every target is a thin wrapper around `uv run ...`, so
# Windows users without make can run the commands shown after each colon directly.
.PHONY: help install lint format format-check typecheck test test-all schemas schemas-check validate demo milestone check clean

help:  ## Show targets
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-14s %s\n", $$1, $$2}'

install:  ## uv sync --extra providers (dev group included by default)
	uv sync --extra providers

lint:  ## uv run ruff check .
	uv run ruff check .

format:  ## uv run ruff format .
	uv run ruff format .

format-check:  ## uv run ruff format --check .
	uv run ruff format --check .

typecheck:  ## uv run mypy
	uv run mypy

test:  ## uv run pytest  (offline; excludes tests marked external)
	uv run pytest

test-all:  ## uv run pytest -m "" (includes external tests; may need network/optional deps)
	uv run pytest -m ""

schemas:  ## uv run python scripts/generate_schemas.py
	uv run python scripts/generate_schemas.py

schemas-check:  ## uv run python scripts/generate_schemas.py --check
	uv run python scripts/generate_schemas.py --check

validate:  ## uv run python scripts/validate_repository.py
	uv run python scripts/validate_repository.py

demo:  ## uv run nr demo  (synthetic, offline, zero cost)
	uv run nr demo

milestone:  ## uv run nr report milestone --output reports/milestone-1-readiness.md
	uv run nr report milestone --output reports/milestone-1-readiness.md

check: lint format-check typecheck test validate  ## Everything CI runs

clean:  ## Remove caches and demo output
	rm -rf .pytest_cache .mypy_cache .ruff_cache experiments/runs/demo
