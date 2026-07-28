---
name: adopt-python-template
description: Use when an active Python or Techletes full-stack repository needs to adopt or update a Techletes template baseline. Establishes the correct upstream and configures the permanent template-sync branch, reusable GitHub Actions callers, first synchronization PR, and reconciliation flow.
---

# Adopt a Techletes Python or Full-Stack Template

Bring an active Python or FastAPI/React repository onto the correct Techletes
template without replacing its application-specific behavior.

The supported hierarchy is:

```text
TECHLETES/python_template -> TECHLETES/full-stack-template -> full-stack project
```

`full-stack-template` itself follows `python_template`. A normal full-stack
project follows `full-stack-template`, not `python_template` directly.

The permanent update model is:

```text
template/main
      | real merge, ancestry retained
      v
chore/template-sync
      | squash PR
      v
staging
      | merge back after squash
      v
chore/template-sync
```

Never merge template updates from a developer feature branch or from a
devcontainer startup hook.

## Use Only When

- The repository is active and Python-based or a Techletes full-stack project.
- No explicit client or product requirement mandates another baseline.
- A separate setup PR and template-sync PR are acceptable.

Stop and report instead of changing files for archived repositories, temporary
scripts, non-Python/non-full-stack repositories, or unclear ownership of
production configuration.

## Choose the Immediate Upstream

Classify the target before changing files:

| Target | Immediate upstream |
|---|---|
| Python-only repository | `TECHLETES/python_template` |
| `TECHLETES/full-stack-template` itself | `TECHLETES/python_template` |
| Full-stack project | `TECHLETES/full-stack-template` |

If the target type or intended parent is unclear, inspect the repository origin,
frontend, compose/deployment files, and branch model, then ask the user before
continuing.

**REQUIRED SUB-SKILL:** Use
`techletes-superpowers:verification-before-completion` before claiming adoption
is complete. Use `techletes-superpowers:systematic-debugging` for merge,
workflow, install, hook, or test failures rather than bypassing them.

## Preflight

1. Read the target repository's `AGENTS.md`, `README.md`, `pyproject.toml`, CI
   workflows, devcontainer files, and branch rules. For full-stack targets, also
   inspect frontend manifests and compose/deployment files.
2. Identify the integration branch. Prefer `staging`; use `main` only when the
   repository intentionally develops directly on `main`.
3. Require a clean working tree. Do not stash, reset, or discard user work.
4. Check whether `.template-sync.yml`, `chore/template-sync`, or either caller
   workflow already exists. Preserve and update a valid setup rather than
   recreating it.
5. Inspect `.devcontainer/post-attach.sh`, `post-create.sh`, and related startup
   scripts for template-fetch or template-merge logic. Remove such logic during
   adoption; opening a devcontainer must not modify Git history.
6. Record the starting branch and commit so work can be abandoned without
   destructive commands.

## Conflict Ownership

Use these rules when choosing the managed-path allowlist and reviewing the first
sync PR:

| Area | Decision |
|---|---|
| Application code, migrations, domain docs | Target-owned |
| Full-stack backend/frontend, generated client, compose, Caddy, deployment | Target-owned unless explicitly governed by the immediate upstream |
| Existing dependencies and package identity | Target-owned; merge tooling carefully |
| `.devcontainer/`, pre-commit, VS Code settings, generic engineering workflows | Usually template-managed, then adapt project-specific paths, services, and ports |
| `pyproject.toml` | Mixed ownership; include only when continuous central governance is intended |
| `uv.lock` | Never hand-merge; regenerate after `pyproject.toml` is final |
| Frontend package and lock files | Usually target-owned |
| Release/deployment workflows | Preserve unless explicitly centrally governed |
| `.env.template` and client configuration | Preserve variables and semantics |
| `README.md` and `AGENTS.md` | Preserve project context unless explicitly centrally governed |
| `.secret.baseline` | Regenerate with the configured tooling; investigate new findings |

Start conservatively. Do not use `**` as a repository-wide allowlist and do not
include mixed-ownership files merely because they exist in the template.

## Initial Setup

The first adoption uses the same permanent synchronization mechanism as later
updates. Do not manually merge the complete upstream template on a temporary
feature branch.

### 1. Create the target-owned sync configuration

Create `.template-sync.yml` in the target repository:

```yaml
source:
  repository: TECHLETES/python_template
  branch: main

target:
  branch: staging
  sync_branch: chore/template-sync

paths:
  # Shared GitHub configuration.
  - .github/workflows/staging-main-check.yml
  - .github/workflows/labeler.yml
  - .github/ISSUE_TEMPLATE/**
  - .github/dependabot.yml
  - .github/pull_request_template.md

  # Shared development environment.
  - .devcontainer/**

  # Shared Python tooling.
  - .pre-commit-config.yaml
  - .python-version
  - .editorconfig
  - .gitattributes
  - pyproject.toml

  # Shared helper scripts.
  - scripts/hooks/**
```

Change the source to `TECHLETES/full-stack-template` for a normal full-stack
project. Change `target.branch` when the repository uses another integration
branch.

The configuration is target-owned and must not list itself under `paths`.
Prefer explicit workflow paths over `.github/workflows/**` when not every
workflow is centrally governed.

### 2. Add the template-sync caller

Create `.github/workflows/template-sync.yml`:

```yaml
name: Sync Python template

on:
  workflow_dispatch:
  schedule:
    - cron: "7 3 * * 1"

jobs:
  sync:
    uses: TECHLETES/python_template/.github/workflows/reusable-template-sync.yml@main

    with:
      template_repository: TECHLETES/python_template
      template_branch: main
      target_branch: staging
      sync_branch: chore/template-sync
      config_path: .template-sync.yml
      pull_request_title: "chore: sync Python template"

    secrets:
      app_client_id: ${{ vars.TEMPLATE_SYNC_APP_CLIENT_ID }}
      app_private_key: ${{ secrets.TEMPLATE_SYNC_APP_PRIVATE_KEY }}
```

For a full-stack project, call the reusable workflow from
`TECHLETES/full-stack-template` and set `template_repository` accordingly when
that repository provides the reusable implementation. Otherwise use the
centrally designated reusable workflow while keeping the configured immediate
upstream accurate.

The caller inputs must exactly match `.template-sync.yml`.

### 3. Add the reconciliation caller

Each target repository needs its own event listener because the merged pull
request event occurs in that repository.

Create `.github/workflows/reconcile-template-sync-branch.yml`:

```yaml
name: Reconcile template sync branch

on:
  pull_request:
    types:
      - closed
    branches:
      - staging

permissions:
  contents: read

concurrency:
  group: template-sync-reconciliation-${{ github.repository }}
  cancel-in-progress: false

jobs:
  reconcile:
    if: >
      github.event.pull_request.merged == true &&
      github.event.pull_request.head.ref == 'chore/template-sync'

    uses: TECHLETES/python_template/.github/workflows/reusable-reconcile-template-sync-branch.yml@main

    with:
      target_branch: staging
      sync_branch: chore/template-sync

    secrets:
      app_client_id: ${{ vars.TEMPLATE_SYNC_APP_CLIENT_ID }}
      app_private_key: ${{ secrets.TEMPLATE_SYNC_APP_PRIVATE_KEY }}
```

Adapt `staging` to the actual integration branch. This file is a small local
caller; the reconciliation implementation stays centralized.

### 4. Merge the bootstrap files into the integration branch

Create a normal setup branch from the current integration branch, add the three
bootstrap files, remove legacy startup merging, run relevant checks, and open a
regular setup PR:

```text
.template-sync.yml
.github/workflows/template-sync.yml
.github/workflows/reconcile-template-sync-branch.yml
```

Do not create the permanent sync branch before these files are merged into the
integration branch.

### 5. Create the initial permanent sync branch

After the setup PR is merged, create `chore/template-sync` directly from the
current integration branch:

```bash
git fetch origin
git switch staging
git pull --ff-only origin staging
git switch -c chore/template-sync
git push -u origin chore/template-sync
```

The initial relationship must be:

```text
chore/template-sync == staging
```

Do not seed the branch with copied template files, an orphan commit, or a manual
upstream merge.

This branch is permanent. Never delete, recreate, rebase, reset, or force-push
it. Its retained merge ancestry records which upstream commits were processed.

Configure a branch ruleset matching exactly `chore/template-sync`:

- enable **Restrict deletions**;
- enable **Block force pushes**;
- do not require linear history;
- do not require pull requests for direct automation updates;
- keep validation checks on the PR into the integration branch;
- retain a restricted maintainer/admin bypass for recovery.

### 6. Run the first sync

Trigger the template-sync caller manually from GitHub Actions.

The reusable workflow must:

1. Check out `chore/template-sync` with full history.
2. Fetch the integration branch and configured immediate upstream.
3. Merge the latest integration branch into the permanent sync branch.
4. Merge the upstream branch with `--allow-unrelated-histories` and create a
   genuine two-parent merge commit.
5. Restore every path outside `.template-sync.yml` to its pre-template state.
6. Resolve unmanaged conflicts in favor of the target.
7. Resolve managed conflicts temporarily to the **template version**, so the
   actual proposed upstream content appears in the PR diff.
8. Push the permanent sync branch.
9. Open or update one PR from `chore/template-sync` to the integration branch.
10. Open the PR as draft when managed conflicts require review.

The workflow must never push directly to `staging` or `main`.

### 7. Review the first sync PR

For ordinary managed changes, review the PR normally.

When the PR says manual template reconciliation is required, the listed files
already contain the template versions and must appear under **Files changed**.
Review those visible changes and restore only the required target-specific
behavior directly on the permanent branch:

```bash
git fetch origin
git switch chore/template-sync
git pull --ff-only origin chore/template-sync

# Edit and test the listed files.

git add <reconciled-files>
git commit -m "chore: reconcile template conflicts"
git push origin chore/template-sync
```

Do not manually compare hidden versions with `git show` unless additional
forensics are needed. The normal review path is the PR diff itself.

After reconciliation:

1. Verify the listed files preserve required target-specific behavior.
2. Remove the manual-reconciliation section and hidden marker from the PR body.
3. Mark the PR ready for review.
4. Run the repository's documented validation.
5. Squash-merge the PR without deleting `chore/template-sync`.

### 8. Verify post-merge reconciliation

After the template PR is squash-merged, the reconciliation caller must merge the
updated integration branch back into `chore/template-sync`.

The expected final relationship is:

```text
integration branch is an ancestor of chore/template-sync
upstream template/main is an ancestor of chore/template-sync
```

If reconciliation conflicts, do not rebase or recreate the permanent branch.
Resolve once on `chore/template-sync`:

```bash
git fetch origin
git switch chore/template-sync
git pull --ff-only origin chore/template-sync
git merge --no-ff origin/staging
# Resolve conflicts.
git add -A
git commit
git push origin chore/template-sync
```

Adapt `staging` to the configured integration branch.

## Later Template Updates

All future updates use the permanent branch and the two caller workflows.

Expected automated sequence:

```text
checkout chore/template-sync
merge current integration branch
merge new upstream template commit
filter to configured paths
apply template versions for managed conflicts
push chore/template-sync
open or update draft/normal PR
squash-merge PR without deleting branch
merge integration branch back into chore/template-sync
```

Never create one-off `chore/update-template` branches and never merge template
updates from `post-attach.sh` or `post-create.sh`.

## Remove Legacy Startup Merging

Remove template-fetch and template-merge logic from devcontainer startup
scripts. A valid `post-attach.sh` may start or restart services only, for example:

```bash
#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${repo_root}"

bash .devcontainer/dev-services.sh restart
```

Opening a devcontainer must never fetch templates, merge branches, stage files,
commit, or push.

## Finish and Verify

Run the repository's documented checks. Typical Python checks are:

```bash
git diff --check
uv lock
uv sync
uv run pre-commit install --install-hooks
uv run pre-commit run --all-files
uv run pytest
```

For full-stack targets, also run the smallest documented frontend lint, type
checking, and test commands. Regenerate the frontend client only when API
changes require it. Follow the target's `AGENTS.md` for Docker restrictions.

Verify the synchronization setup:

- `.template-sync.yml` points to the correct immediate upstream and integration
  branch;
- its allowlist includes only deliberately governed paths and excludes the
  configuration itself;
- both local caller workflows exist on the integration branch;
- `chore/template-sync` was created from the current integration branch;
- the permanent branch contains the upstream merge ancestry after the first
  sync;
- the ruleset blocks deletion and force pushes while permitting merge commits;
- the template-sync workflow has a schedule and manual trigger;
- the sync PR uses the permanent branch as head and the integration branch as
  base;
- template-conflicted managed files are visible in the draft PR diff;
- the PR is squash-merged without deleting the permanent branch;
- post-merge reconciliation brings the integration branch back into the
  permanent branch;
- legacy devcontainer merge logic is gone;
- existing deployment workflows remain present;
- no real secrets entered the repository or secret baseline.

## Completion Evidence

The setup or adoption PR must state:

- selected immediate upstream;
- target integration branch;
- `.template-sync.yml` managed paths and intentional exclusions;
- caller workflow locations and schedule;
- permanent sync branch creation status;
- branch ruleset status;
- first sync PR status and any reconciled managed conflicts;
- post-merge reconciliation result;
- validation results, including frontend checks when applicable;
- devcontainer result or documented reason it was not run;
- secret-baseline result and any legacy gaps.

Do not claim completion when the configuration, callers, permanent branch,
first sync PR, required reconciliation, or removal of startup merging is still
missing.
