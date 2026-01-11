.PHONY: help setup install run clean test

help:
	@echo "StreamsToFiles - Makefile Commands"
	@echo "===================================="
	@echo ""
	@echo "Available targets:"
	@echo "  make setup    - Initialize uv environment and install dependencies"
	@echo "  make install  - Install package in development mode"
	@echo "  make run      - Run with default example playlist"
	@echo "  make clean    - Remove output files and build artifacts"
	@echo "  make test     - Run tests (not yet implemented)"
	@echo "  make help     - Show this help message"
	@echo ""

setup:
	@echo "Setting up development environment..."
	@command -v uv >/dev/null 2>&1 || { echo "Error: uv is not installed. Install from https://docs.astral.sh/uv/"; exit 1; }
	uv sync

install: setup
	@echo "Installing package in development mode..."
	uv pip install -e .

run:
	@echo "Running streamstofiles with default playlist..."
	uv run streamstofiles

clean:
	@echo "Cleaning up..."
	rm -rf files/
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf src/*.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "Clean complete!"

test:
	@echo "Tests not yet implemented"
	@echo "TODO: Add pytest tests"
