#!/usr/bin/env bash

set -e
set -x

uv run black .
uv run mypy .
uv run ruff check .
uv run ruff format . --check
