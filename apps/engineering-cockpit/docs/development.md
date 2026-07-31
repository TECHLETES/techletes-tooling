# Techletes Development Setup

## Quick Start

### Prerequisites

- Docker
- VS Code Dev Containers
- uv and Bun are installed by the devcontainer bootstrap

### 1. Full Stack Development

Open the repository in the devcontainer. On first create, `post-create.sh` will:

- create `.env` from `.env.template` if needed
- run `uv sync`
- install frontend dependencies with `bun install`
- install pre-commit hooks when `.git` is present

On every attach, `post-attach.sh` starts the frontend and backend dev servers in the background with hot reload.

**Services:**
- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`
- Adminer: forwarded from the devcontainer
- Mailpit: forwarded from the devcontainer

### Manage Dev Services

Use the devcontainer helper script when you need control over the background services:

```bash
bash .devcontainer/dev-services.sh start
bash .devcontainer/dev-services.sh restart
bash .devcontainer/dev-services.sh stop
bash .devcontainer/dev-services.sh status
```

Service logs are written to `logs/frontend-dev.log` and `logs/backend-dev.log`.

### Local Only Development

If you are not using the devcontainer, run the frontend and backend separately from their own directories.

## Development Workflow

### Making Backend Changes

1. Edit files in `backend/`
2. Let the backend dev service reload automatically, or restart it with `bash .devcontainer/dev-services.sh restart`
3. Run tests with `cd backend && ./scripts/test.sh`
4. Run lint with `cd backend && ./scripts/lint.sh`
5. If the API changed, regenerate the frontend client with `bash ./scripts/generate-client.sh`
6. Check API docs at `http://localhost:8000/api/v1/docs`

### Making Frontend Changes

1. Edit files in `frontend/src/`
2. Let the frontend dev service reload automatically, or restart it with `bash .devcontainer/dev-services.sh restart`
3. Run tests with `cd frontend && bun run test`
4. Run lint with `cd frontend && bun run lint`
5. Run type checks with `cd frontend && bun run typecheck`
6. Regenerate the client after API changes with `bash ./scripts/generate-client.sh`
7. Use `bun run i18n:extract`, `bun run i18n:types`, and `bun run i18n:status` when changing UI strings

### Database Changes

1. Edit models in `backend/models.py`
2. Restart the backend dev service after changing models so startup checks and migrations rerun: `bash .devcontainer/dev-services.sh restart`
3. Create a migration with `cd backend && uv run alembic revision --autogenerate -m "description"`
4. Apply it with `cd backend && uv run alembic upgrade head`

## Environment Setup

### `.env` Configuration

The devcontainer bootstraps `.env` from `.env.template` when needed. Update it with:

- `SECRET_KEY` - Generate with `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- `FIRST_SUPERUSER`
- `FIRST_SUPERUSER_PASSWORD`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_DB`
- `DOMAIN`
- `FRONTEND_HOST`
- `BACKEND_CORS_ORIGINS`

For local Compose development, `FRONTEND_HOST` is usually `http://localhost`.

### Database

- In the devcontainer, PostgreSQL runs in the `db` service.
- If you expose PostgreSQL locally yourself, the default port is `5432`.
- User: `postgres` by default in the devcontainer stack
- Database: `app` by default

## Testing

```bash
# Backend tests
cd backend && ./scripts/test.sh

# Backend lint
cd backend && ./scripts/lint.sh

# Frontend tests
cd frontend && bun run test
```

## Troubleshooting

### Backend Issues

- Check `logs/backend-dev.log`
- Restart the backend service: `bash .devcontainer/dev-services.sh restart`
- If the container just started, let `post-create.sh` finish `uv sync`

### Frontend Issues

- Check `logs/frontend-dev.log`
- Restart the frontend service: `bash .devcontainer/dev-services.sh restart`
- If dependencies look stale, re-run the devcontainer `post-create.sh` bootstrap

### Database Issues

- Restart the devcontainer compose services from VS Code or rerun the devcontainer
- Adminer and Mailpit are forwarded from the devcontainer ports, not exposed by a separate local Compose setup

## Project Structure

```text
workspace/
├── backend/          # FastAPI backend
│   ├── tests/        # Backend tests
│   ├── scripts/      # Backend helper scripts
│   └── alembic/      # Database migrations
├── frontend/         # React frontend
│   ├── src/          # Source code
│   └── tests/        # Playwright tests
├── docs/             # Documentation
├── docker-compose.yml
├── Caddyfile
└── Dockerfile
```

## Need Help?

- Architecture: `docs/specs/FRONTEND-ARCHITECTURE.md`
- Backend Guide: `docs/backend.instructions.md`
- Frontend Guide: `docs/frontend.instructions.md`
- Deployment: `docs/deployment.md`
- Release Notes: `docs/release-notes.md`
