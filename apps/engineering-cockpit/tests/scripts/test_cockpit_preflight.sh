#!/usr/bin/env bash
set -euo pipefail

test_root="$(mktemp -d)"
trap 'rm -rf "$test_root"' EXIT
mkdir -p "$test_root/bin"

for tool in docker devcontainer codex uv bun node curl git gh; do
  cat > "$test_root/bin/$tool" <<'EOF'
#!/usr/bin/env bash
if [[ "${1:-}" == "--version" || "${1:-}" == "version" ]]; then
  echo "test-version"
fi
EOF
  chmod +x "$test_root/bin/$tool"
done

set +e
output="$(PATH="$test_root/bin:$PATH" COCKPIT_PREFLIGHT_TEST_ROOT="$test_root" bash scripts/cockpit-preflight.sh 2>&1)"
status=$?
set -e
printf '%s\n' "$output"
[[ "$status" -eq 0 ]]
grep -F 'WSL/Linux' <<<"$output"
grep -F 'Docker' <<<"$output"
grep -F 'Dev Container CLI' <<<"$output"
grep -F 'Codex CLI' <<<"$output"
