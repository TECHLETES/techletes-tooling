---
name: Techletes Full-Stack Template — Workspace Instructions
description: Concise workspace rules for FastAPI, React, PostgreSQL, and the service-first frontend architecture
---

# Techletes Full-Stack Template — Workspace Instructions

## Template Bootstrap for New Repositories

This repository is a reusable template. When a coding agent starts work in a
repository created from this template, its first implementation action must be
to update `AGENTS.md` and `README.md` for the current repository and project.
Do this before changing application code, adding dependencies, or starting
feature work.

The bootstrap pass must:

- Inspect the current `pyproject.toml`, source and test directories, docs,
  workflows, and available development commands before writing project
  context.
- Replace generic template descriptions with the actual project name,
  purpose, architecture, entry points, repository structure, setup path, and
  verification commands.
- Add concise project-specific instructions for important workflows,
  boundaries, integrations, data handling, deployment, and known pitfalls.
- Update the README's overview, features, structure, setup, usage, and links
  so they describe the current project rather than the template examples.
- Preserve the template's generally applicable coding standards, security
  rules, dependency workflow, type-checking requirements, tool configuration,
  and verification expectations unless the current repository has an explicit
  and documented replacement.
- Base every project-specific instruction on the repository's actual files and
  commands. Do not invent architecture, scripts, services, or requirements.
- Review the documentation diff and run the smallest relevant documentation or
  repository checks before continuing with implementation.

When working on this template repository itself, keep the general guidance
maintained here and in `README.md`, and describe the template's intended
bootstrap behavior instead of replacing it with a downstream project's
context.

---

## Purpose

This repository is Techletes' internal full-stack template for FastAPI, SQLModel, PostgreSQL, React, TypeScript, Vite, and shadcn/ui. Keep changes aligned with the current docs and prefer concise, maintainable patterns over repeated inline instructions.

Primary references:

- [frontend.instructions.md](.github/instructions/frontend.instructions.md)
- [backend.instructions.md](.github/instructions/backend.instructions.md)
- [docs/specs/FRONTEND-ARCHITECTURE.md](docs/specs/FRONTEND-ARCHITECTURE.md)
- [docs/specs/TRANSLATIONS.md](docs/specs/TRANSLATIONS.md)
- [docs/specs/RBAC-SYSTEM.md](docs/specs/RBAC-SYSTEM.md)
- [docs/development.md](docs/development.md)
- [docs/deployment.md](docs/deployment.md)

## Non-Negotiables

1. Do not run `docker compose up` or `docker compose build` for development unless explicitly asked.
2. Use `docker-compose.dev.yml` only for base services when PostgreSQL or Redis are needed and not already available locally.
3. Run backend and frontend locally by default.
4. Keep frontend code service-first: components and hooks use `@/services`, and `@/client` is for generated types and service-layer internals only.
5. Keep route nesting correct for TanStack Router: layout routes render `<Outlet />`, and default children live in `index.tsx`.
6. Keep UI aligned with [frontend/design-brief.json](frontend/design-brief.json).

## Quick Commands

### Backend

```bash
cd backend
uv sync
./scripts/run-dev.sh
./scripts/test.sh
./scripts/lint.sh
```

### Frontend

```bash
cd frontend
bun install
bun run dev
bun run generate-client
bun run lint
bun run typecheck
bun run test
```

Use `bun run generate-client` after backend API changes. Do not hand-edit generated files.

## Backend Rules

- FastAPI route code lives in `backend/api/routes/`.
- SQLModel models live in `backend/models.py`.
- Database changes require Alembic migrations.
- Return API response models, not table models.
- Keep auth, DB, and config logic in the existing core modules.

See [backend.instructions.md](instructions/backend.instructions.md) for backend-specific conventions.

## Frontend Rules

- Use the service layer in `frontend/src/services/` for runtime API calls.
- Use feature hooks in `frontend/src/hooks/` for React Query state and mutations.
- Keep components presentational where possible.
- Use `useCustomToast()` for user-facing success and error feedback.
- Use typed imports from `@/client` only for generated types.
- Prefer plain function components and hooks; do not add class components.
- Use dynamic translation keys and `useTranslation` for user-facing strings. Do not hardcode strings in components. Use scripts/hooks/check-frontend-translations.sh to validate after implementation.

See [frontend.instructions.md](instructions/frontend.instructions.md) and [docs/specs/FRONTEND-ARCHITECTURE.md](docs/specs/FRONTEND-ARCHITECTURE.md) for examples.

## Testing

- Backend: `./scripts/test.sh`
- Frontend lint/typecheck: `bun run lint` and `bun run typecheck`
- Frontend E2E: `bun run test`
- Use Playwright and backend test fixtures that already exist in the repo.

Prefer the smallest useful validation step for the area you changed. If you touch backend models, run the migration flow. If you touch frontend API usage, regenerate the client and typecheck.

## Environment

Key frontend environment variables:

- `VITE_API_URL`

Key backend environment variables:

- `SECRET_KEY`
- `DATABASE_URL`
- `ENVIRONMENT`
- `FIRST_SUPERUSER`
- `FIRST_SUPERUSER_PASSWORD`
- `SMTP_HOST`
- `SMTP_PORT`
- `BACKEND_CORS_ORIGINS`

## Entra Integration

Microsoft Entra support is already documented and implemented as an opt-in feature. Use [docs/ENTRA_SETUP.md](docs/ENTRA_SETUP.md) and the auth docs instead of repeating setup steps here.

## When To Ask

Ask before making architecture changes that affect:

- route structure or guards
- service/hook boundaries
- auth flows
- database migrations
- frontend design changes that affect the design brief

## Short Version

If in doubt, keep changes small, keep runtime API calls out of components, regenerate the client after backend API changes, and defer detailed implementation guidance to the linked docs.
