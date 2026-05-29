# Techletes Coding Wrapper

CLI tools for enforcing branch naming conventions and running pre-flight checks.

## Allowed Branches

| Type | Allowed values |
| --- | --- |
| Bare branch names | `main`, `staging`, `develop`, `master` |
| Prefixes | `feature/`, `bug/`, `refactor/`, `security/`, `breaking/`, `question/`, `docs/` |

## Usage

### Validate branch names

Check an explicit branch name:

```bash
python scripts/validate-branch-name.py feature/add-login
```

Check the currently checked-out branch:

```bash
python scripts/validate-branch-name.py
```

Successful validation prints the branch name followed by `VALID` and exits with status `0`. Invalid branch names print `INVALID` plus the allowed bare branches and prefixes, then exit with status `1`.

### Run pre-flight checks

Run all repository pre-flight checks from the repo root:

```bash
bash scripts/preflight.sh
```

The script runs these checks in order:

1. `uv lock --check`
2. `pre-commit run --all-files`
3. `uv run pytest` from `backend/` if that directory exists, otherwise from the repo root

Each step prints a clear status line with `✅` or `❌`.

## Install as a pre-commit hook

To use the branch validator in another project, add this repository as a pre-commit hook source and point the hook entry at the validator script:

```yaml
repos:
  - repo: https://github.com/<your-org>/techletes-tooling
    rev: main
    hooks:
      - id: validate-branch-name
        name: validate-branch-name
        entry: python scripts/validate-branch-name.py
        language: system
        pass_filenames: false
```

If you are working from a local checkout instead of a published Git repo, use a local path-based `repo: local` entry that runs the same command.

### GitHub Webhook Auth Proxy

This repository now includes a standalone ASGI proxy that authorizes GitHub webhooks before forwarding them to a Hermes gateway.

Build dependencies:

```bash
pip install fastapi uvicorn
```

If you are using `uv`, the equivalent is:

```bash
uv add fastapi uvicorn
```

Create `~/.hermes/github-webhook-proxy.json` from `config/github-proxy.yaml.example`.

Run the proxy directly:

```bash
python -m uvicorn github_proxy.main:app --host 0.0.0.0 --port 8655
```

Or use the launcher script:

```bash
bash scripts/github-proxy.sh
```

Example systemd unit:

```ini
[Unit]
Description=GitHub Webhook Authorization Proxy
After=network.target

[Service]
Type=simple
WorkingDirectory=/home/techadmin/work/repos/techletes-tooling
Environment=GITHUB_PROXY_HOST=0.0.0.0
Environment=GITHUB_PROXY_PORT=8655
ExecStart=/home/techadmin/work/repos/techletes-tooling/scripts/github-proxy.sh
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Test the local health endpoint:

```bash
curl -X POST http://localhost:8655/health
```
