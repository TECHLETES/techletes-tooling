#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"

if ! command -v bun >/dev/null 2>&1; then
  echo "bun is required to run the frontend translation check." >&2
  exit 1
fi

cd "$repo_root/frontend"

echo "Checking frontend translations..."
bun run i18n:check
