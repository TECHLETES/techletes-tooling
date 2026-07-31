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

for hook_and_file in \
    "check-json apps/engineering-cockpit/frontend/openapi.json" \
    "end-of-file-fixer apps/engineering-cockpit/frontend/src/client/generated/index.ts" \
    "end-of-file-fixer apps/engineering-cockpit/coverage.svg" \
    "trailing-whitespace apps/engineering-cockpit/frontend/src/client/generated/index.ts" \
    "trailing-whitespace apps/engineering-cockpit/coverage.svg" \
    "bandit apps/engineering-cockpit/backend/tests/cockpit/test_runtime_instance.py" \
    "pydocstyle apps/engineering-cockpit/backend/tests/cockpit/test_runtime_instance.py"; do
    read -r hook file <<<"$hook_and_file"
    output="$(uv run --project "$app_root" pre-commit run "$hook" \
        --config "$config" --files "$file" 2>&1)"
    printf '%s\n' "$output"
    grep -F 'Skipped' <<<"$output"
done

mypy_output="$(uv run --project "$app_root" pre-commit run mypy \
    --config "$config" --files apps/engineering-cockpit/backend/main.py 2>&1)"
printf '%s\n' "$mypy_output"
grep -F 'Passed' <<<"$mypy_output"

secret_output="$(uv run --project "$app_root" pre-commit run detect-secrets \
    --config "$config" --files apps/engineering-cockpit/.techletes-template-source.yml 2>&1)"
printf '%s\n' "$secret_output"
grep -F 'Passed' <<<"$secret_output"

lock_path_output="$(
    cd "$app_root"
    SECRET_KEY=scope-test-secret-key-with-more-than-32-characters \
    FRONTEND_HOST=http://localhost:5173 \
    PROJECT_NAME=scope-test \
    POSTGRES_SERVER=localhost \
    POSTGRES_USER=scope-test \
    POSTGRES_PASSWORD=scope-test-password \
    POSTGRES_DB=scope-test \
    FIRST_SUPERUSER=scope-test@example.com \
    FIRST_SUPERUSER_PASSWORD=scope-test-password \
    REDIS_URL=redis://localhost:6379 \
    XDG_RUNTIME_DIR=/run/user/1234 uv run python -c \
        'from backend.main import _default_lock_path; print(_default_lock_path())'
)"
printf '%s\n' "$lock_path_output"
grep -Fx '/run/user/1234/techletes-engineering-cockpit.lock' <<<"$lock_path_output"
