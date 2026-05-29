#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"

if [ -f "$repo_root/.venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  . "$repo_root/.venv/bin/activate"
fi

cd "$repo_root"

exec uvicorn github_proxy.main:app --host "${GITHUB_PROXY_HOST:-0.0.0.0}" --port "${GITHUB_PROXY_PORT:-8655}"

