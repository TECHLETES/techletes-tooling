#!/usr/bin/env bash
set -euo pipefail

techletes-dev doctor

python --version 2>&1 | grep -Eq '^Python 3\.12\.'
uv --version | grep -Fq '0.12.13'
node --version | grep -Eq '^v22\.'
bun --version | grep -Fxq '1.4.2'
codex --version | grep -Fq '0.154.0'
az --version | grep -Fq 'azure-cli'
psql --version | grep -Eq ' 18\.'
odbcinst -q -d | grep -qi 'mariadb'
mariadb_config --version >/dev/null

if [[ "$(id -un)" != "vscode" ]]; then
  echo "Expected image user 'vscode', got '$(id -un)'." >&2
  exit 1
fi

echo 'Pinned shared devcontainer image checks passed.'
