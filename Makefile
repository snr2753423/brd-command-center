# BRD Command Center — common local targets
#
# Assumptions:
#   - GNU Make (or compatible) and a Unix shell
#   - Python 3.11+ on PATH as python3 (3.12 preferred; matches CI)
#   - Optional for CI: GitHub Actions still runs pip + pytest directly
#
# Usage: make help | make install | make test | make run | make asgi

PYTHON ?= python3
VENV   ?= .venv
BIN    := $(VENV)/bin

.DEFAULT_GOAL := help

.PHONY: help install test run asgi

help:
	@echo "BRD Command Center — make targets"
	@echo ""
	@echo "  make install   Create $(VENV)/ and pip install -r requirements.txt"
	@echo "  make test      Run pytest (run make install first)"
	@echo "  make run       Launch Streamlit (streamlit_app.py)"
	@echo "  make asgi      Launch uvicorn app:app --reload"
	@echo "  make help      Show this help (default)"
	@echo ""
	@echo "Requires Python 3.11+ (3.12 preferred). On Windows use WSL/Git Bash"
	@echo "or the README venv commands. CI does not depend on this Makefile."

install:
	$(PYTHON) -m venv $(VENV)
	$(BIN)/pip install -r requirements.txt

test:
	$(BIN)/pytest

run:
	$(BIN)/streamlit run streamlit_app.py

asgi:
	$(BIN)/uvicorn app:app --reload
