#!/usr/bin/env bash
set -u -o pipefail

status=0

check() {
  local label="$1"
  shift
  local output
  if output=$("$@" 2>&1); then
    printf '✅ %-20s %s\n' "$label" "${output//$'\n'/; }"
  else
    printf '❌ %-20s unavailable\n' "$label" >&2
    status=1
  fi
}

if [[ "$(uname -s)" == "Linux" ]] && grep -qi microsoft /proc/version; then
  printf '✅ %-20s WSL/Linux\n' "WSL/Linux"
else
  printf '❌ %-20s required\n' "WSL/Linux" >&2
  status=1
fi

check "Docker" docker version --format '{{.Server.Version}}'
check "Docker Compose" docker compose version

if command -v devcontainer >/dev/null 2>&1; then
  check "Dev Container CLI" devcontainer --version
elif command -v bunx >/dev/null 2>&1; then
  check "Dev Container CLI" bunx --bun @devcontainers/cli --version
else
  printf '❌ %-20s unavailable\n' "Dev Container CLI" >&2
  status=1
fi

check "Codex CLI" codex --version
check "Python" python3 --version
check "uv" uv --version
check "Bun" bun --version
check "Node.js" node --version
check "curl" curl --version
check "Git" git --version
check "GitHub CLI" gh --version

exit "$status"
