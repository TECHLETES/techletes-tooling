#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
app_root="$repo_root/apps/engineering-cockpit"
config="$app_root/.pre-commit-config.yaml"

cd "$repo_root"

before_status="$(git status --short)"
trap 'after_status="$(git status --short)"; test "$after_status" = "$before_status"' EXIT

root_output="$(uv run --project "$app_root" pre-commit run check-yaml \
  --config "$config" --files .github/workflows/engineering-cockpit-ci.yml 2>&1)"
printf '%s\n' "$root_output"
grep -F 'Skipped' <<<"$root_output"

app_output="$(uv run --project "$app_root" pre-commit run check-yaml \
  --config "$config" --files apps/engineering-cockpit/docker-compose.local-services.yml 2>&1)"
printf '%s\n' "$app_output"
grep -F 'Passed' <<<"$app_output"
