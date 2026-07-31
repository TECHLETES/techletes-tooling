#!/bin/bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# Set PYTHONPATH to the repository root so `backend.*` imports resolve no matter
# where this script is launched from.
export PYTHONPATH="${repo_root}${PYTHONPATH:+:$PYTHONPATH}"

cd "${repo_root}/backend"

# Verify the database and backend prerequisites.
uv run python -m backend.utils.backend_pre_start

echo "🔄 Running database migrations..."
uv run alembic upgrade head

echo "🌱 Initializing database with sample data..."
uv run python -m backend.utils.initial_data

echo "✨ Starting FastAPI development server..."
exec uv run fastapi dev main.py --host 0.0.0.0
