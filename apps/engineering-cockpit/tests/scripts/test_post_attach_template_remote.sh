#!/usr/bin/env bash
set -euo pipefail

test_root="$(mktemp -d)"
trap 'rm -rf "${test_root}"' EXIT

mkdir -p "${test_root}/repo/.devcontainer" "${test_root}/bin"
cp .devcontainer/post-attach.sh "${test_root}/repo/.devcontainer/post-attach.sh"

cat > "${test_root}/bin/sudo" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "$*" >> "${TEST_ROOT}/sudo-calls"
exec "$@"
EOF

cat > "${test_root}/bin/curl" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "$*" >> "${TEST_ROOT}/curl-calls"
exit 99
EOF

cat > "${test_root}/bin/npm" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "$*" >> "${TEST_ROOT}/npm-calls"
exit 0
EOF

cat > "${test_root}/bin/git" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

printf 'unexpected git invocation: %s\n' "$*" >&2
exit 1
EOF
chmod +x "${test_root}/bin/sudo" "${test_root}/bin/curl" "${test_root}/bin/npm" "${test_root}/bin/git"

output="$({
  cd "${test_root}/repo"
  PATH="${test_root}/bin:${PATH}" TEST_ROOT="${test_root}" DEVCONTAINER_CI=true \
    bash .devcontainer/post-attach.sh
} 2>&1)"

[[ "${output}" == *"Skipping private Codex plugin setup in CI."* ]]
[[ "$(<"${test_root}/sudo-calls")" == "npm install -g @openai/codex" ]]
[[ "$(<"${test_root}/npm-calls")" == "install -g @openai/codex" ]]
[[ ! -e "${test_root}/curl-calls" ]]
