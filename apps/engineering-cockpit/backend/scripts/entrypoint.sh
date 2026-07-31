#!/usr/bin/env bash
set -e

# =============================================================================
# Docker Entrypoint for FastAPI Backend
# Handles prestart tasks and server initialization with production-ready config
# =============================================================================

# Get environment variables with sensible defaults
ENVIRONMENT="${ENVIRONMENT:-local}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
WORKERS="${WORKERS:-4}"
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

export PYTHONPATH="${repo_root}${PYTHONPATH:+:$PYTHONPATH}"

echo "[Entrypoint] Starting FastAPI Backend Initialization"
echo "[Entrypoint] Environment: $ENVIRONMENT"
echo "[Entrypoint] Workers: $WORKERS"

RUNTIME_API_URL="$FRONTEND_HOST"

write_frontend_runtime_config() {
    local target_dir="$1"
    local escaped_api_url

    mkdir -p "$target_dir"
    escaped_api_url=$(printf '%s' "$RUNTIME_API_URL" | sed 's/\\/\\\\/g; s/"/\\"/g')

    cat > "$target_dir/env.js" <<EOF
window.__APP_CONFIG__ = {
  apiUrl: "$escaped_api_url",
};
EOF
}

if [ -d /app/backend/static ]; then
    echo "[Entrypoint] Syncing frontend build for Caddy..."
    mkdir -p /app/frontend-dist
    rm -rf /app/frontend-dist/*
    cp -a /app/backend/static/. /app/frontend-dist/
    write_frontend_runtime_config /app/backend/static
    write_frontend_runtime_config /app/frontend-dist
fi

cd "${repo_root}/backend"

# Step 1: Wait for database to be ready
echo "[Entrypoint] Step 1/3: Waiting for database..."
python -m backend.utils.backend_pre_start
if [ $? -ne 0 ]; then
    echo "[Entrypoint] ERROR: Database pre-start checks failed"
    exit 1
fi

# Step 2: Run database migrations (BEFORE RBAC initialization)
echo "[Entrypoint] Step 2/3: Running database migrations..."
alembic upgrade head
if [ $? -ne 0 ]; then
    echo "[Entrypoint] ERROR: Database migrations failed"
    exit 1
fi

# Step 3: Create initial data
echo "[Entrypoint] Step 3/3: Initializing database with seed data..."
python -m backend.utils.initial_data
if [ $? -ne 0 ]; then
    echo "[Entrypoint] ERROR: Initial data creation failed"
    exit 1
fi

echo "[Entrypoint] Initialization complete. Starting FastAPI server..."
echo "[Entrypoint] Listening on port $BACKEND_PORT"

# Build fastapi command based on configuration
FASTAPI_CMD="fastapi run --port $BACKEND_PORT --workers $WORKERS"

# Use exec to replace shell process with FastAPI, preserving PID signals
exec $FASTAPI_CMD main.py
