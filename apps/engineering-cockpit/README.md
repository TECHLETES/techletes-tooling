# Techletes Engineering Cockpit

This directory is reserved for the Techletes Engineering Cockpit implementation.

## Bootstrap requirement

The application must be bootstrapped from the current `TECHLETES/full-stack-template` before cockpit-specific implementation starts. Preserve the template's existing FastAPI/React structure, devcontainer, CI, dependency management, typing, linting, testing, and pre-commit conventions. Adapt the plans to the actual current template layout rather than creating a parallel structure.

## Authoritative planning documents

- [Product specification](superpowers/spec/2026-07-31-engineering-cockpit-design.md)
- [Implementation plan](superpowers/implementation/2026-07-31-engineering-cockpit-implementation-plan.md)

The GitHub tracking issue is `TECHLETES/techletes-tooling#7`.

## Primary runtime decision

The cockpit backend runs in WSL and launches `codex app-server` inside each task's devcontainer through `devcontainer exec`. The backend owns the app-server process and communicates using structured JSON-RPC over stdin/stdout. Terminal scraping and tmux are not the primary orchestration mechanism.
