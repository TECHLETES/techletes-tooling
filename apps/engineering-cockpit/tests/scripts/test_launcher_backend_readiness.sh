#!/usr/bin/env bash
set -euo pipefail

test_root="$(mktemp -d)"
trap 'rm -rf "${test_root}"' EXIT

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
if [[ " $* " == *" uvicorn "* ]]; then
  exit 1
fi
exit 0
EOF

cat > "${test_root}/bin/bun" <<'EOF'
#!/usr/bin/env bash
printf 'frontend-started\n' > "${TEST_ROOT}/frontend-started"
EOF

chmod +x "${test_root}/bin/docker" "${test_root}/bin/uv" "${test_root}/bin/bun"

set +e
launcher_output="$(
  cd "${test_root}"
  PATH="${test_root}/bin:${PATH}" TEST_ROOT="${test_root}" \
    bash scripts/cockpit-dev.sh 2>&1
)"
launcher_status=$?
set -e

printf '%s\n' "${launcher_output}"
[[ "${launcher_status}" -ne 0 ]]
[[ ! -e "${test_root}/frontend-started" ]]
grep -F 'backend exited before becoming ready' <<<"${launcher_output}"
