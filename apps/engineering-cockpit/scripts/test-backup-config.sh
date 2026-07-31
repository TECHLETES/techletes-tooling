#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
env_file="$repo_root/.env"
run_backup=false

if [[ "${1:-}" == --run ]]; then
  run_backup=true
  shift
fi
[[ $# -eq 0 ]] || { echo "Usage: test-backup-config.sh [--run]" >&2; exit 2; }

die() {
  echo "Error: $*" >&2
  exit 1
}

command -v docker >/dev/null 2>&1 || die "required command not found: docker"
[[ -f "$env_file" ]] || die "missing .env; copy .env.template and set backup values"

required_vars=(
  BACKUP_CRON_EXPRESSION BACKUP_RETENTION_DAYS
  BACKUP_FILENAME BACKUP_PRUNING_PREFIX AZURE_STORAGE_ACCOUNT_NAME
  AZURE_STORAGE_CONTAINER_NAME AZURE_STORAGE_CONNECTION_STRING
)
for variable in "${required_vars[@]}"; do
  grep -Eq "^${variable}=[^[:space:]]|^${variable}=.+$" "$env_file" || die "missing non-secret .env value: $variable"
done

compose=(docker compose -f "$repo_root/docker-compose.yml")
config_file="$(mktemp)"
cleanup() {
  rm -f "$config_file"
}
trap cleanup EXIT

"${compose[@]}" config --quiet >/dev/null || die "docker compose config failed"
"${compose[@]}" config >"$config_file"
"${compose[@]}" config --services | grep -Fxq backup || die "backup service is missing"
grep -Fq '/database_backups:/backup/database:ro' "$config_file" || die "database dump volume is not mounted at /backup/database"
grep -Fq '/uploads-data:/backup/uploads:ro' "$config_file" || die "uploads volume is not mounted at /backup/uploads"

container_id="$("${compose[@]}" ps -q backup)"
[[ -n "$container_id" ]] || die "backup service is not running; start it before checking container paths"
"${compose[@]}" exec -T backup sh -c 'test -d /backup/database && test -d /backup/uploads' || die "backup container cannot see expected /backup paths"

if [[ "$run_backup" == true ]]; then
  "${compose[@]}" run --rm --entrypoint backup backup
fi

echo "Backup configuration is valid; expected mounts are visible in the running backup container."
