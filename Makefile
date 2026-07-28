MAKEFLAGS += --warn-undefined-variables
SHELL := bash

# allow overriding which dependency groups are installed
VENV_GROUPS ?= --group dev --group docs

# set default lit options
LIT_OPTIONS ?= -v --order=smart


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
tests: pytest filecheck

.PHONY: pytest
pytest: .venv/
	uv run pytest -W error --cov

.PHONY: filecheck
filecheck: .venv/
	uv run lit $(LIT_OPTIONS) tests/filecheck

.PHONY: docs
docs: .venv/
	uv run mkdocs serve
	uv run mkdocs build

.PHONY: json-format
json-format: .venv/
	uv run python -m jsonmlir.schema_gen --output .

.PHONY: examples-test
examples-test: .venv/
	MLIR_BIN_DIR=$(MLIR_BIN_DIR) uv run pytest -s --maxfail=0 tests/test_examples.py

.PHONY: examples examples-array examples-somme
examples: examples-array examples-somme

examples-array: .venv/
	MLIR_BIN_DIR=$(MLIR_BIN_DIR) uv run python src/jsonmlir/cli.py compile examples/array_read.json
	./examples/array.out

examples-somme: .venv/
	MLIR_BIN_DIR=$(MLIR_BIN_DIR) uv run python src/jsonmlir/cli.py compile examples/somme.json
	./examples/somme.out

# Répertoire des binaires MLIR/LLVM (override : make MLIR_BIN_DIR=…)
MLIR_BIN_DIR ?= $(HOME)/code/llvm-project/build-mlir/bin

clean-caches:
	rm -rf .mypy_cache/ .pytest_cache/ .ruff_cache/ .coverage
	find . -not -path "./.venv/*" | \
		grep -E "(/__pycache__$$|\.pyc$$|\.pyo$$)" | \
		xargs rm -rf

.PHONY: clean
clean: clean-caches
	rm -rf ${VENV_DIR}
