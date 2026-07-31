# Techletes Engineering Cockpit

Engineering Cockpit is a local-first FastAPI and React control plane for
launching, monitoring, interacting with, reviewing, and delivering multiple
Codex development tasks. Each task has its own branch, linked worktree,
devcontainer, app-server connection, and mutable state.

The application lives in `apps/engineering-cockpit/` within
[`TECHLETES/techletes-tooling`](https://github.com/TECHLETES/techletes-tooling).
The implementation plan and subsystem specifications are indexed in
[`superpowers/README.md`](superpowers/README.md). The planning issue is
[`TECHLETES/techletes-tooling#7`](https://github.com/TECHLETES/techletes-tooling/issues/7).

## Development mode

Open `apps/engineering-cockpit/` in its devcontainer. The devcontainer
provides the application workspace plus PostgreSQL, Redis, Adminer, and
Mailpit. Run the backend and frontend locally inside that environment:

```bash
cd backend
uv sync
./scripts/run-dev.sh
```

In another terminal:

```bash
cd frontend
bun install
bun run dev
```

For checks, use `cd backend && ./scripts/test.sh && ./scripts/lint.sh`, then
`cd frontend && bun run lint && bun run typecheck && bun run build`.
Use `bun run generate-client` after changing the backend API.

## Host operational mode

Normal operation runs the control plane directly in WSL, with exactly one
FastAPI/Uvicorn process and one worker. This gives the backend controlled access
to host Git, Docker, the Dev Container CLI, and Codex app-server stdio. Bind
the browser, PostgreSQL, and Redis services to loopback addresses only. Task
code and its Codex process still run in the task's isolated target
devcontainer; the browser is not the process owner.

Use the repository's bootstrap/runtime preflight and launcher scripts when they
are available. Do not start multiple operational workers or expose services on
all interfaces.

## Required WSL tools

Install and verify these tools in WSL before host operation:

- WSL2 with a working Linux distribution
- Python 3.12+ and `uv`
- Node.js and Bun
- Docker Engine or Docker Desktop integration with WSL
- Docker Compose and the Dev Container CLI
- Git and the GitHub CLI (`gh`)
- Codex CLI at the version required by the pinned app-server schemas

Do not put credentials or secret values in this repository. Configure runtime
secrets through the existing environment and secret-management workflow.

## Repository layout

- `backend/` — FastAPI control plane, persistence, runtime adapters, and tests
- `frontend/` — React/Vite dashboard and generated API client
- `.devcontainer/` — development services and target workspace configuration
- `superpowers/` — authoritative subsystem specifications and implementation
  plans
- `scripts/` — repository-level helper and verification scripts

## Bootstrap provenance

This application was imported from the current
`TECHLETES/full-stack-template` snapshot. The exact source commit is recorded
in `.techletes-template-source.yml`; subsequent work specializes the baseline
for Engineering Cockpit while retaining its tested FastAPI, PostgreSQL, React,
TypeScript, and tooling conventions.
