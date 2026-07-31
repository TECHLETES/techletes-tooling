#!/usr/bin/env bash
set -euo pipefail

if rg -n -i 'fullstack template|fullstack-template' \
  frontend/src/routes/_layout/admin-tasks.tsx \
  frontend/src/routes/_layout/unauthorized.tsx; then
  echo "stale template identity remains in cockpit routes" >&2
  exit 1
fi

rg -n 'Engineering Cockpit' \
  frontend/src/routes/_layout/admin-tasks.tsx \
  frontend/src/routes/_layout/unauthorized.tsx >/dev/null
