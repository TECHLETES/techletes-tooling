#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"
export PYTHONPATH="$repo_root${PYTHONPATH:+:$PYTHONPATH}"

env_file="$repo_root/.env.local"
die() {
  echo "Error: $*" >&2
  exit 1
}

[[ -r "$env_file" ]] || die "missing readable .env.local; copy .env.local.example and set local values"

# Read simple KEY=VALUE dotenv entries without evaluating the file. This keeps
# command substitutions and other shell syntax in local configuration inert.
line_number=0
while IFS= read -r line || [[ -n "$line" ]]; do
  line_number=$((line_number + 1))
  trimmed="${line#"${line%%[![:space:]]*}"}"
  [[ -z "$trimmed" || "${trimmed:0:1}" == "#" ]] && continue
  [[ "$trimmed" =~ ^([a-zA-Z_][a-zA-Z0-9_]*)=(.*)$ ]] || \
    die "invalid entry in .env.local at line $line_number"
  key="${BASH_REMATCH[1]}"
  value="${BASH_REMATCH[2]}"
  printf -v "$key" '%s' "$value"
  export "$key"
done < "$env_file"

[[ -n "${POSTGRES_PASSWORD:-}" ]] || die "POSTGRES_PASSWORD must be set in .env.local"

# The support-services ports are host ports; give Alembic and Uvicorn the same
# local endpoints that Compose exposes, without logging any configuration.
export POSTGRES_SERVER="${POSTGRES_SERVER:-127.0.0.1}"
export POSTGRES_PORT="${POSTGRES_PORT:-${COCKPIT_POSTGRES_PORT:-55432}}"
export REDIS_URL="${REDIS_URL:-redis://127.0.0.1:${COCKPIT_REDIS_PORT:-56379}/0}"

bash scripts/cockpit-preflight.sh
bash scripts/cockpit-services-up.sh
cd backend

backend_pid=""
frontend_pid=""
cleanup() {
  kill "$backend_pid" "$frontend_pid" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

uv run python -c '
import os
import sys

from backend.cockpit.runtime_instance import RuntimeInstanceLock, runtime_lock_path
from backend.cockpit.runtime_instance import RuntimeInstanceAlreadyRunning

try:
    lock = RuntimeInstanceLock.acquire(runtime_lock_path())
except RuntimeInstanceAlreadyRunning as exc:
    print(f"Error: {exc}", file=sys.stderr)
    raise SystemExit(1) from None
file_descriptor = lock.fileno()
os.set_inheritable(file_descriptor, True)
os.environ["COCKPIT_INHERITED_LOCK_FD"] = str(file_descriptor)
os.execv(sys.executable, [sys.executable, "-m", "uvicorn", *sys.argv[1:]])
' uvicorn backend.main:app \
  --host 127.0.0.1 \
  --port "${COCKPIT_BACKEND_PORT:-8000}" \
  --workers 1 &
backend_pid=$!

backend_url="http://127.0.0.1:${COCKPIT_BACKEND_PORT:-8000}/api/v1/utils/health-check/"
backend_ready=0
for _ in {1..50}; do
  if ! kill -0 "$backend_pid" 2>/dev/null; then
    wait "$backend_pid" 2>/dev/null || true
    die "backend exited before becoming ready"
  fi
  if curl --fail --silent --max-time 1 "$backend_url" >/dev/null 2>&1; then
    backend_ready=1
    break
  fi
  sleep 0.2
done

if (( backend_ready == 0 )); then
  die "backend did not become ready"
fi

uv run alembic upgrade head

cd ../frontend
bun run dev --host 127.0.0.1 \
  --port "${COCKPIT_FRONTEND_PORT:-5173}" &
frontend_pid=$!
wait -n "$backend_pid" "$frontend_pid"
