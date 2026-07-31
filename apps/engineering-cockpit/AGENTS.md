---
name: Techletes Engineering Cockpit — Workspace Instructions
description: Project rules for the local-first WSL control plane and target-task development environment
---

# Techletes Engineering Cockpit

## Project context

Engineering Cockpit is a local-first control plane for launching and
supervising Codex development tasks across repositories. The operational
backend runs natively in WSL as one FastAPI process and one Uvicorn worker. It
owns host paths, Docker/Dev Container CLI calls, and long-lived app-server
stdio connections. PostgreSQL is durable state; Redis is only a live wakeup
mechanism.

The application was bootstrapped from the current
`TECHLETES/full-stack-template` snapshot recorded in
`.techletes-template-source.yml`; adapt its conventions rather than creating a
competing scaffold.

The target repository for a task runs in its own linked worktree and
devcontainer. Codex runs inside that target devcontainer through the backend's
owned `codex app-server` stdio connection. Do not use TUI scraping, multiple
operational Uvicorn workers, or guessed host paths and commands.

Detailed subsystem specifications and plans are indexed in
[`superpowers/README.md`](superpowers/README.md).

## Non-negotiables

- Keep browser, PostgreSQL, and Redis exposure loopback-only in local mode.
- Treat PostgreSQL as the source of truth; Redis notifications are disposable.
- Preserve authentication, authorization, validation, recovery, and audit
  boundaries at trust boundaries.
- Do not automatically replay lost turns, answer questions or approvals, merge
  changes, deploy, or delete branches, worktrees, or volumes.
- Use generated app-server protocol schemas from the exact pinned Codex
  version. Do not hand-roll or scrape protocol output.
- Prefer the existing architecture and dependencies. Keep changes small and
  add a focused test for non-trivial behavior.

## Development and validation

Development uses the repository devcontainer for the application workspace and
its PostgreSQL, Redis, Adminer, and Mailpit support services. Run backend and
frontend commands locally in that environment; do not use `docker compose up`
or `docker compose build` as an ad-hoc development shortcut.

Backend commands, from `apps/engineering-cockpit/backend/`:

```bash
uv sync
./scripts/test.sh
./scripts/lint.sh
```

Frontend commands, from `apps/engineering-cockpit/frontend/`:

```bash
bun install
bun run lint
bun run typecheck
bun run build
bun run test
```

After backend API changes, regenerate the typed frontend client with
`bun run generate-client`. Never hand-edit generated client files.

Host operational mode is WSL-native, single-process, and loopback-bound. It
exists so the control plane can reach the host Git, Docker, Dev Container CLI,
and Codex installation; target task execution remains inside isolated target
devcontainers. Use the project bootstrap/runtime launcher and preflight checks
when they are present rather than starting a second Uvicorn worker manually.

## Repository conventions

- FastAPI routes live in `backend/api/routes/`; SQLModel models live in the
  existing backend model modules.
- Database changes require Alembic migrations.
- Frontend runtime API calls go through `frontend/src/services/`; generated
  types are imported from `@/client`.
- User-facing strings use the existing i18n resources.
- Never commit credentials, copied Codex auth, secret values, or complete
  environment dumps.

When a change affects task isolation, authentication, protocol schemas,
recovery, delivery, or cleanup, read the matching numbered specification and
implementation plan before editing code.
