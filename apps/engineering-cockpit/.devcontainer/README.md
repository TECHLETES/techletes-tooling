# Devcontainer

Use this folder to boot and manage the local dev environment inside VS Code.

## Start

1. create `.env` from `.env.template` and set secrets
2. Open the repo in a Dev Container.
3. Let `post-create.sh` finish the first setup:
   - creates `.env` from `.env.template` if needed
   - runs `uv sync`
   - installs frontend dependencies with `bun install`
   - installs pre-commit hooks when `.git` is present
4. On each attach, `post-attach.sh` starts the app services.

## Services

- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`
- Compose services: `db`, `redis`, `adminer`, `mailcatcher`

## Manage services

Use the VS Code tasks or run the script directly:

```bash
bash .devcontainer/dev-services.sh start
bash .devcontainer/dev-services.sh restart
bash .devcontainer/dev-services.sh stop
bash .devcontainer/dev-services.sh status
```

## Logs

- Service logs: `logs/frontend-dev.log`, `logs/backend-dev.log`, and `logs/worker-dev.log`
- The `logs/` directory is created automatically

## Notes

- `post-attach.sh` keeps frontend and backend running after the terminal closes.
- If the frontend looks stuck, check `logs/frontend-dev.log` first.
