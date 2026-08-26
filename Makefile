MAKEFLAGS += --warn-undefined-variables
SHELL := bash

# allow overriding which dependency groups are installed
VENV_GROUPS ?= --group dev


.PHONY: install
install: .venv/

.venv/:
	uv sync ${VENV_GROUPS}

.PHONY: check
check: .venv/
	uv run ruff check src tests
	uv run ruff format --check src tests

.PHONY: pyright
pyright: .venv/
	uv run pyright $(shell git diff --staged --name-only  -- '*.py')

.PHONY: tests
tests: pytest

.PHONY: pytest
pytest: .venv/
	uv run pytest -W error --cov

clean-caches:
	rm -rf .mypy_cache/ .pytest_cache/ .ruff_cache/ .coverage
	find . -not -path "./.venv/*" | \
		grep -E "(/__pycache__$$|\.pyc$$|\.pyo$$)" | \
		xargs rm -rf

.PHONY: clean
clean: clean-caches
	rm -rf ${VENV_DIR}
