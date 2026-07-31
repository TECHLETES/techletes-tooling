#!/usr/bin/env bash
set -euo pipefail

launcher="scripts/cockpit-dev.sh"
pythonpath_line="$(grep -nF 'export PYTHONPATH="$repo_root${PYTHONPATH:+:$PYTHONPATH}"' "$launcher" | cut -d: -f1)"
backend_line="$(grep -nF 'cd backend' "$launcher" | cut -d: -f1)"
alembic_line="$(grep -nF 'subprocess.run(["uv", "run", "alembic", "upgrade", "head"]' "$launcher" | cut -d: -f1)"
uvicorn_line="$(grep -nF "' uvicorn backend.main:app" "$launcher" | cut -d: -f1)"

[[ -n "$pythonpath_line" ]]
(( pythonpath_line < backend_line ))
(( alembic_line < uvicorn_line ))
