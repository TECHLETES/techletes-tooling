#!/usr/bin/env bash

set -euo pipefail

compose_file="docker-compose.local-services.yml"
grep -F 'name: techletes-engineering-cockpit' "$compose_file"
grep -F '127.0.0.1:${COCKPIT_POSTGRES_PORT:-55432}:5432' "$compose_file"
grep -F '127.0.0.1:${COCKPIT_REDIS_PORT:-56379}:6379' "$compose_file"
! grep -E '(^|[[:space:]])-[[:space:]]*"?(0\.0\.0\.0:)?(5432|6379):' "$compose_file"
