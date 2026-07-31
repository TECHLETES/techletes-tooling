#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

[[ "$(uname -s)" == "Linux" ]]
grep -qi microsoft /proc/version

bash scripts/cockpit-services-up.sh
cd backend
uv run alembic upgrade head
uv run uvicorn backend.main:app \
  --host 127.0.0.1 \
  --port "${COCKPIT_BACKEND_PORT:-8000}" \
  --workers 1 &
backend_pid=$!
cd ../frontend
bun run dev --host 127.0.0.1 \
  --port "${COCKPIT_FRONTEND_PORT:-5173}" &
frontend_pid=$!
trap 'kill "$backend_pid" "$frontend_pid" 2>/dev/null || true' EXIT INT TERM
wait -n "$backend_pid" "$frontend_pid"
