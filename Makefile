.PHONY: help setup install run rerandomize clean test

# Optional variables (override on command line)
PLAYLIST_URL ?=
PLAYLIST_DIR ?=

help:
	@echo "StreamsToFiles - Makefile Commands"
	@echo "===================================="
	@echo ""
	@echo "Available targets:"
	@echo "  make setup                           - Initialize uv environment and install dependencies"
	@echo "  make install                         - Install package in development mode"
	@echo "  make run [PLAYLIST_URL=<url>]        - Run with default or provided playlist"
	@echo "  make rerandomize PLAYLIST_DIR=<path> - Re-randomize existing tracks in a directory"
	@echo "  make clean                           - Remove output files and build artifacts"
	@echo "  make test                            - Run tests (not yet implemented)"
	@echo "  make help                            - Show this help message"
	@echo ""

setup:
	@echo "Setting up development environment..."
	@command -v uv >/dev/null 2>&1 || { echo "Error: uv is not installed. Install from https://docs.astral.sh/uv/"; exit 1; }
	uv sync

install: setup
	@echo "Installing package in development mode..."
	uv pip install -e .

run:
ifdef PLAYLIST_URL
	@echo "Running streamstofiles with provided playlist..."
	@bash -c 'source ~/.bashrc 2>/dev/null || source ~/.zshrc 2>/dev/null || true; uv run streamstofiles "$(PLAYLIST_URL)"'
else
	@echo "Running streamstofiles with default playlist..."
	@bash -c 'source ~/.bashrc 2>/dev/null || source ~/.zshrc 2>/dev/null || true; uv run streamstofiles'
endif

rerandomize:
ifndef PLAYLIST_DIR
	@echo "Error: PLAYLIST_DIR is required"
	@echo "Usage: make rerandomize PLAYLIST_DIR=files/My_Playlist/"
	@exit 1
endif
	@echo "Re-randomizing tracks in $(PLAYLIST_DIR)..."
	@bash -c 'source ~/.bashrc 2>/dev/null || source ~/.zshrc 2>/dev/null || true; uv run rerandomize "$(PLAYLIST_DIR)"'

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
