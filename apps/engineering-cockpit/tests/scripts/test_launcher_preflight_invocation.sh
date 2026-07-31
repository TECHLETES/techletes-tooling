#!/usr/bin/env bash
set -euo pipefail

source_root="$PWD"
test_root="$(mktemp -d)"
trap 'rm -rf "$test_root"' EXIT
mkdir -p "$test_root/scripts" "$test_root/bin"
cp scripts/cockpit-dev.sh "$test_root/scripts/cockpit-dev.sh"
cp scripts/cockpit-services-up.sh "$test_root/scripts/cockpit-services-up.sh"
printf 'POSTGRES_PASSWORD=test-password\n' > "$test_root/.env.local"

cat > "$test_root/scripts/cockpit-preflight.sh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
: > "${TEST_ROOT}/preflight-ran"
EOF

cat > "$test_root/bin/docker" <<'EOF'
#!/usr/bin/env bash
exit 0
EOF
chmod +x "$test_root/scripts/cockpit-preflight.sh" "$test_root/bin/docker"

set +e
(cd "$test_root" && PATH="$test_root/bin:$PATH" TEST_ROOT="$test_root" \
  SOURCE_ROOT="$source_root" COCKPIT_INSTANCE_LOCK_PATH="$test_root/instance.lock" \
  timeout 5 bash scripts/cockpit-dev.sh) >/dev/null 2>&1
status=$?
set -e

[[ "$status" -ne 0 ]]
[[ -e "$test_root/preflight-ran" ]]
