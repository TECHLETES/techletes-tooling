#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
env_file="$repo_root/.env.local"
compose_file="$repo_root/docker-compose.local-services.yml"
project_name="techletes-engineering-cockpit"

die() {
  echo "Error: $*" >&2
  exit 1
}

[[ -f "$env_file" ]] || die "missing .env.local; copy .env.local.example and set a local password"
grep -Eq '^POSTGRES_PASSWORD=[^[:space:]]+$' "$env_file" || \
  die "POSTGRES_PASSWORD must be set in .env.local"
command -v docker >/dev/null 2>&1 || die "required command not found: docker"

docker compose \
  --env-file "$env_file" \
  -f "$compose_file" \
  -p "$project_name" \
  up -d --wait

postgres_port="$(grep -E '^COCKPIT_POSTGRES_PORT=' "$env_file" | tail -n 1 | cut -d= -f2- || true)"
redis_port="$(grep -E '^COCKPIT_REDIS_PORT=' "$env_file" | tail -n 1 | cut -d= -f2- || true)"
postgres_port="${postgres_port:-55432}"
redis_port="${redis_port:-56379}"
printf 'PostgreSQL: 127.0.0.1:%s\nRedis:       127.0.0.1:%s\n' "$postgres_port" "$redis_port"
