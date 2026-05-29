#!/usr/bin/env bash
set -u -o pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"

cd "$repo_root"

status=0

run_step() {
  local label="$1"
  shift

  printf '%s %s\n' "▶️" "$label"
  if "$@"; then
    printf '%s %s\n' "✅" "$label"
  else
    printf '%s %s\n' "❌" "$label"
    status=1
  fi
}

run_step "uv lock --check" uv lock --check
run_step "pre-commit run --all-files" pre-commit run --all-files

if [ -d "$repo_root/backend" ]; then
  pytest_dir="$repo_root/backend"
else
  pytest_dir="$repo_root"
fi

run_pytest() {
  cd "$pytest_dir" && uv run pytest
}

run_step "uv run pytest ($pytest_dir)" run_pytest

exit "$status"
