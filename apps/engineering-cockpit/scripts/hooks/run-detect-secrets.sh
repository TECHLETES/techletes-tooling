#!/usr/bin/env bash
# Run detect-secrets with the repository's shared file exclusions.
#
# Normal mode scans with .secret.baseline and reviews findings interactively;
# Pre-commit mode uses detect-secrets-hook so the committed
# baseline is enforced without modifying it or starting an audit.

set -euo pipefail

usage() {
    cat <<'EOF'
Usage:
  scripts/hooks/run-detect-secrets.sh [--non-interactive]
  scripts/hooks/run-detect-secrets.sh --pre-commit [files ...]

Normal mode scans with .secret.baseline and reviews findings interactively;
--non-interactive is retained as an explicit no-audit alias. --pre-commit checks
the files supplied by pre-commit without changing the baseline.
EOF
}

MODE="scan"
POSITIONAL=()

while (($# > 0)); do
    case "$1" in
        --help|-h)
            usage
            exit 0
            ;;
        --non-interactive)
            MODE="non-interactive"
            shift
            ;;
        --pre-commit)
            MODE="pre-commit"
            shift
            ;;
        --)
            shift
            POSITIONAL+=("$@")
            break
            ;;
        *)
            POSITIONAL+=("$1")
            shift
            ;;
    esac
done

EXCLUDE_REGEX="$(uv run python - <<'PY'
from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path


try:
    with Path("pyproject.toml").open("rb") as config_file:
        config = tomllib.load(config_file)
except (OSError, tomllib.TOMLDecodeError) as exc:
    print(f"Error reading pyproject.toml: {exc}", file=sys.stderr)
    raise SystemExit(1) from exc

exclude_files = config.get("tool", {}).get("detect-secrets", {}).get(
    "exclude_files", []
)

if not isinstance(exclude_files, list) or not all(
    isinstance(pattern, str) for pattern in exclude_files
):
    print(
        "[tool.detect-secrets].exclude_files must be a list of strings",
        file=sys.stderr,
    )
    raise SystemExit(1)

try:
    for pattern in exclude_files:
        re.compile(pattern)
except re.error as exc:
    print(f"Invalid detect-secrets exclude regex: {exc}", file=sys.stderr)
    raise SystemExit(1) from exc

print("|".join(f"(?:{pattern})" for pattern in exclude_files))
PY
)"

EXCLUDE_ARGS=()
if [[ -n "$EXCLUDE_REGEX" ]]; then
    EXCLUDE_ARGS=(--exclude-files "$EXCLUDE_REGEX")
fi

BASELINE_BACKUP=""
PROGRESS_PID=""
cleanup() {
    if [[ -n "$PROGRESS_PID" ]]; then
        kill "$PROGRESS_PID" 2>/dev/null || true
        wait "$PROGRESS_PID" 2>/dev/null || true
    fi
    if [[ -n "$BASELINE_BACKUP" ]]; then
        rm -f "$BASELINE_BACKUP"
    fi
}
trap cleanup EXIT

run_scan_with_progress() {
    if [[ ! -t 1 ]]; then
        "$@"
        echo "Secret scan complete."
        return 0
    fi

    "$@" &
    local scan_pid=$!
    local frames='|/-\\'
    local frame_index=0

    (
        while kill -0 "$scan_pid" 2>/dev/null; do
            printf '\rScanning repository for secrets... %s' "${frames:frame_index:1}"
            frame_index=$(( (frame_index + 1) % ${#frames} ))
            sleep 0.2
        done
    ) &
    PROGRESS_PID=$!

    local scan_status=0
    if wait "$scan_pid"; then
        scan_status=0
    else
        scan_status=$?
    fi

    kill "$PROGRESS_PID" 2>/dev/null || true
    wait "$PROGRESS_PID" 2>/dev/null || true
    PROGRESS_PID=""
    printf '\r\033[K'

    if [[ "$scan_status" -eq 0 ]]; then
        echo "Secret scan complete."
    else
        echo "Secret scan failed (exit code $scan_status)." >&2
    fi
    return "$scan_status"
}

if [[ "$MODE" == "pre-commit" ]]; then
    if [[ -f .secret.baseline ]]; then
        BASELINE_BACKUP="$(mktemp)"
        cp .secret.baseline "$BASELINE_BACKUP"
    fi

    if uv run detect-secrets-hook \
        --baseline .secret.baseline \
        "${EXCLUDE_ARGS[@]}" \
        "${POSITIONAL[@]}"; then
        exit 0
    else
        hook_status=$?
    fi

    # Exit code 3 only means the baseline was refreshed (usually line numbers).
    # Potential secrets use exit code 1 and must still fail pre-commit.
    if [[ "$hook_status" -eq 3 ]]; then
        if [[ -n "$BASELINE_BACKUP" ]]; then
            cp "$BASELINE_BACKUP" .secret.baseline
        fi
        exit 0
    fi
    exit "$hook_status"
fi

if ((${#POSITIONAL[@]} > 0)); then
    echo "Unexpected positional arguments in scan mode: ${POSITIONAL[*]}" >&2
    usage >&2
    exit 2
fi

if [[ -f .secret.baseline ]]; then
    BASELINE_BACKUP="$(mktemp)"
    cp .secret.baseline "$BASELINE_BACKUP"
fi

run_scan_with_progress \
    uv run detect-secrets scan --baseline .secret.baseline "${EXCLUDE_ARGS[@]}"

# detect-secrets refreshes generated_at on every scan. Avoid a working-tree
# change when the scan found no substantive baseline changes.
if [[ -n "$BASELINE_BACKUP" ]] && uv run python - "$BASELINE_BACKUP" .secret.baseline <<'PY'
import json
import sys
from pathlib import Path


def comparable(path: str) -> dict[str, object]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    data.pop("generated_at", None)
    return data


raise SystemExit(comparable(sys.argv[1]) != comparable(sys.argv[2]))
PY
then
    cp "$BASELINE_BACKUP" .secret.baseline
fi

# Keep the generated baseline with the scan that produced it. Leave an
# already-staged baseline untouched so callers can review their staged version.
if git diff --cached --quiet -- .secret.baseline; then
    git add .secret.baseline
fi

if [[ "$MODE" == "non-interactive" || ! -t 0 || ! -t 1 ]]; then
    echo "Skipping detect-secrets audit because no interactive terminal is available."
    echo "Run 'scripts/hooks/run-detect-secrets.sh' in the devcontainer to audit."
    exit 0
fi

exec uv run detect-secrets audit .secret.baseline
