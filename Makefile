.PHONY: help install run test lint

help:
	@echo "Available targets:"
	@echo "  install  Install the package and dev dependencies"
	@echo "  run      Start the API server (hot-reload)"
	@echo "  test     Run the full test suite"
	@echo "  lint     Run ruff linter over src/, scripts/, and tests/"

install:
	pip install -e ".[dev]"

run:
	uvicorn able_to_answer.api.main:app --reload --host 0.0.0.0 --port 8000

test:
	python -m pytest tests/ -v

lint:
	ruff check src/ scripts/ tests/
