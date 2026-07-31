#!/usr/bin/env bash
set -euo pipefail

source_root="$PWD"
test_root="$(mktemp -d)"
lock_path="${test_root}/runtime/instance.lock"
holder_pid=""
trap 'if [[ -n "$holder_pid" ]]; then kill "$holder_pid" 2>/dev/null || true; wait "$holder_pid" 2>/dev/null || true; fi; rm -rf "$test_root"' EXIT

mkdir -p "${test_root}/scripts" "${test_root}/backend" "${test_root}/frontend" "${test_root}/bin"
cp scripts/cockpit-dev.sh "${test_root}/scripts/cockpit-dev.sh"
cp scripts/cockpit-services-up.sh "${test_root}/scripts/cockpit-services-up.sh"
printf '#!/usr/bin/env bash\nexit 0\n' > "${test_root}/scripts/cockpit-preflight.sh"
chmod +x "${test_root}/scripts/cockpit-preflight.sh"
printf 'POSTGRES_PASSWORD=test-password\n' > "${test_root}/.env.local"

cat > "${test_root}/bin/docker" <<'EOF'
#!/usr/bin/env bash
exit 0
EOF

cat > "${test_root}/bin/uv" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
if [[ "${1:-}" == "run" && "${2:-}" == "python" ]]; then
  shift 2
  PYTHONPATH="${SOURCE_ROOT}" exec python3 "$@"
fi
if [[ " $* " == *" alembic "* ]]; then
  : > "${TEST_ROOT}/migration-started"
  exit 0
fi
if [[ " $* " == *" uvicorn "* ]]; then
  : > "${TEST_ROOT}/backend-started"
  exit 1
fi
exit 0
EOF

cat > "${test_root}/bin/bun" <<'EOF'
#!/usr/bin/env bash
: > "${TEST_ROOT}/frontend-started"
EOF

chmod +x "${test_root}/bin/docker" "${test_root}/bin/uv" "${test_root}/bin/bun"

COCKPIT_INSTANCE_LOCK_PATH="$lock_path" PYTHONPATH="$source_root" \
  python3 -c '
from pathlib import Path
import os
import time

from backend.cockpit.runtime_instance import RuntimeInstanceLock

lock = RuntimeInstanceLock.acquire(Path(os.environ["COCKPIT_INSTANCE_LOCK_PATH"]))
print("ready", flush=True)
time.sleep(30)
lock.release()
' > "${test_root}/holder-output" &
holder_pid=$!
for _ in {1..50}; do
  grep -q '^ready$' "${test_root}/holder-output" && break
  sleep 0.02
done
grep -q '^ready$' "${test_root}/holder-output"

set +e
launcher_output="$(
  cd "${test_root}"
  PATH="${test_root}/bin:${PATH}" TEST_ROOT="${test_root}" SOURCE_ROOT="${source_root}" \
    COCKPIT_INSTANCE_LOCK_PATH="$lock_path" bash scripts/cockpit-dev.sh 2>&1
)"
launcher_status=$?
set -e

printf '%s\n' "${launcher_output}"
[[ "${launcher_status}" -ne 0 ]]
grep -F 'control plane already running' <<<"${launcher_output}"
[[ ! -e "${test_root}/migration-started" ]]
[[ ! -e "${test_root}/backend-started" ]]
[[ ! -e "${test_root}/frontend-started" ]]
