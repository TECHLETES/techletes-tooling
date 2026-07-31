#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
env_file="$repo_root/.env.local"
compose_file="$repo_root/docker-compose.local-services.yml"
project_name="techletes-engineering-cockpit"

command -v docker >/dev/null 2>&1 || {
  echo "Error: required command not found: docker" >&2
  exit 1
}

compose_args=(--env-file "$env_file")
if [[ ! -f "$env_file" ]]; then
  compose_args=()
  export POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-unused-for-down}"
fi

docker compose \
  "${compose_args[@]}" \
  -f "$compose_file" \
  -p "$project_name" \
  down
