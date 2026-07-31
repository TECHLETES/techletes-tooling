# Azure Blob Storage Backups Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use techletes-superpowers:subagent-driven-development (recommended) or techletes-superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an optional Docker Compose backup override that archives persistent volumes and native PostgreSQL dumps to per-environment Azure Blob containers.

**Architecture:** Extend the production `docker-compose.yml` with the backup service, dedicated dump volume, lifecycle labels, direct Azure connection-string environment variable, and read-only volume mounts. Provide guarded Azure provisioning and local configuration-test scripts, plus environment templates and operator documentation.

**Tech Stack:** Docker Compose, `offen/docker-volume-backup:v2`, PostgreSQL `pg_dump`, Bash, Azure CLI, Markdown.

## Global Constraints

- Azure storage account is `techletesbackups`; containers are `docker-<app>-<environment>`.
- Default schedule is daily at 03:00 in `Europe/Amsterdam`; retention is 30 days.
- SAS is container-scoped, HTTPS-only, never committed, printed, or silently overwritten.
- PostgreSQL live data, Redis data, build artifacts, virtual environments, source, and temporary data are not backed up.
- Do not provision Azure resources during implementation; local validation must not require Azure credentials.

### Task 1: Compose backup configuration

**Files:** Modify `docker-compose.yml` and `.env.template`.

- [ ] Add `database_backups` to `db`, with PostgreSQL lifecycle labels that create and remove `/database-backups/database.dump` using `POSTGRES_PASSWORD` and escaped Compose dollars.
- [ ] Add the `backup` service to the normal Compose stack with required image, schedule/retention/name variables, direct Azure connection string, read-only Docker socket, database dump mount, uploads mount, and commented guidance for optional durable volumes.
- [ ] Add backup variables, the Azure connection-string placeholder, and the `{{ .Extension }}` interpolation warning to `.env.template`; keep real server `.env` values out of Git.

### Task 2: Provisioning and verification scripts

**Files:** Create `scripts/setup-azure-backup.sh` and `scripts/test-backup-config.sh`.

- [ ] Implement validated dry-run-by-default Azure container/SAS provisioning with `az account show`, private container creation, container-scoped `racwdl` SAS, optional IP restriction, and terminal connection-string output without writing secrets.
- [ ] Implement required `.env` variable, Compose, service, mount, and optional one-off backup checks without exposing values.

### Task 3: Documentation and references

**Files:** Create `docs/AZURE-BACKUPS.md`; modify `README.md`.

- [ ] Document prerequisites, authentication, automated/manual provisioning, configuration, volume selection, PostgreSQL dump/restore, start/test/verify/rotate procedures, and required troubleshooting cases.
- [ ] Add a concise top-level README link explaining that backups are optional and provisioned per environment.

### Task 4: Verification

- [ ] Run Bash syntax, JSON validation, ShellCheck when available, Compose rendering, script configuration checks that can run without Azure, and Git/secret scans.
- [ ] Review the complete diff and report changed files, assumptions, and Azure-permission steps still required.
