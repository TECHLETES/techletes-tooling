# Engineering Cockpit Superpowers Planning

The Engineering Cockpit is specified as a master architecture plus independently implementable subsystem specification/plan pairs.

## Authoritative entry points

1. [`INDEX.md`](INDEX.md)
2. [`00-engineering-cockpit-master-specification.md`](00-engineering-cockpit-master-specification.md)
3. [`00-engineering-cockpit-master-implementation-roadmap.md`](00-engineering-cockpit-master-implementation-roadmap.md)

The historical monolithic design and implementation plan remain under `spec/` and `implementation/` as background only. They are superseded and must not be executed as the current implementation plan.

## Implementation workflow

- Read the master specification and roadmap.
- Start with subsystem 01 and the current `TECHLETES/full-stack-template`.
- Before each subsystem, read its child specification and implementation plan from [`INDEX.md`](INDEX.md).
- Use `techletes-superpowers:using-superpowers`, then `techletes-superpowers:subagent-driven-development` or `techletes-superpowers:executing-plans` as directed by the child plan.
- Complete the subsystem's tests, integration gate, manual/real acceptance, commits, and exit criteria before proceeding.
- Treat generated schemas, migrations, clients, route trees, compatibility manifests, and release evidence as reviewed versioned artifacts.

## Critical cross-cutting requirements

- Operational backend is host-native in WSL, one process/Uvicorn worker.
- Every task has a separate branch, linked worktree, devcontainer runtime, app-server connection, thread, and mutable state.
- Linked worktree Git metadata must be mounted and verified inside each task devcontainer; see subsystem 05a.
- `codex app-server` over backend-owned stdio is the primary integration.
- PostgreSQL is durable truth; Redis provides live event wakeups.
- Questions/approvals persist before notification and map to exact protocol request IDs.
- Browser disconnect never stops work; backend restart never claims old stdio ownership.
- Validation, commit, push, PR, force, and cleanup actions are explicit, exact-state, authorized, idempotent, and audited.
- No TUI scraping, merge, auto-merge, deployment, broad prune, plain force, hook/signing bypass, or arbitrary command/path execution.
