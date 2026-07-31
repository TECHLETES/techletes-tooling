#! /usr/bin/env bash

set -e
set -x

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
backend_dir="$repo_root/backend"
frontend_dir="$repo_root/frontend"
client_dir="$frontend_dir/src/client"
tmp_openapi="$(mktemp "$frontend_dir/openapi.json.tmp.XXXXXX")"

cleanup() {
	rm -f "$tmp_openapi"
}

remove_obsolete_client_files() {
	rm -rf \
		"$client_dir/client" \
		"$client_dir/core" \
		"$client_dir/client.gen.ts" \
		"$client_dir/schemas.gen.ts" \
		"$client_dir/sdk.gen.ts" \
		"$client_dir/types.gen.ts"
}

trap cleanup EXIT

cd "$backend_dir"
PYTHONPATH="$repo_root${PYTHONPATH:+:$PYTHONPATH}" \
	uv run python -c "import backend.main; import json; print(json.dumps(backend.main.app.openapi()))" > "$tmp_openapi"
mv "$tmp_openapi" "$frontend_dir/openapi.json"
trap - EXIT

cd "$repo_root/frontend"
remove_obsolete_client_files
bun run generate-client
bun run lint
