#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

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
