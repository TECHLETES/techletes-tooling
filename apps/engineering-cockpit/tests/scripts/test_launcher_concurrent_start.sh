#!/usr/bin/env bash
set -euo pipefail

source_root="$PWD"
test_root="$(mktemp -d)"
trap 'if [[ -n "${first_pid:-}" ]]; then kill "$first_pid" 2>/dev/null || true; wait "$first_pid" 2>/dev/null || true; fi; rm -rf "$test_root"' EXIT
mkdir -p "$test_root/scripts" "$test_root/backend" "$test_root/frontend" "$test_root/bin"
cp scripts/cockpit-dev.sh "$test_root/scripts/cockpit-dev.sh"
cp scripts/cockpit-services-up.sh "$test_root/scripts/cockpit-services-up.sh"
cp -R backend/cockpit "$test_root/backend/"
printf 'POSTGRES_PASSWORD=test-password\n' > "$test_root/.env.local"

cat > "$test_root/bin/docker" <<'EOF'
#!/usr/bin/env bash
exit 0
EOF
cat > "$test_root/bin/uv" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
if [[ "${1:-}" == run && "${2:-}" == python ]]; then
  shift 2
  PYTHONPATH="${SOURCE_ROOT}" exec python3 -c '
import os
import time
from pathlib import Path

from backend.cockpit.runtime_instance import RuntimeInstanceLock, runtime_lock_path

lock = RuntimeInstanceLock.acquire(runtime_lock_path())
Path(os.environ["TEST_ROOT"], "backend-started").touch()
time.sleep(30)
'
fi
if [[ " $* " == *" alembic "* ]]; then
  : > "${TEST_ROOT}/migration-started"
  exit 0
fi
if [[ " $* " == *" uvicorn "* ]]; then
  : > "${TEST_ROOT}/backend-started"
  sleep 30
fi
EOF
cat > "$test_root/bin/bun" <<'EOF'
#!/usr/bin/env bash
: > "${TEST_ROOT}/frontend-started"
EOF
chmod +x "$test_root/bin"/*

set +e
(cd "$test_root" && PATH="$test_root/bin:$PATH" TEST_ROOT="$test_root" SOURCE_ROOT="$source_root" \
  COCKPIT_INSTANCE_LOCK_PATH="$test_root/instance.lock" bash scripts/cockpit-dev.sh) &
first_pid=$!
sleep 1
second_output="$(cd "$test_root" && PATH="$test_root/bin:$PATH" TEST_ROOT="$test_root" SOURCE_ROOT="$source_root" \
  COCKPIT_INSTANCE_LOCK_PATH="$test_root/instance.lock" timeout 5 bash scripts/cockpit-dev.sh 2>&1)"
second_status=$?
set -e

printf '%s\n' "$second_output"
[[ "$second_status" -ne 0 ]]
grep -F 'control plane already running' <<<"$second_output"
[[ ! -e "$test_root/frontend-started" ]]
