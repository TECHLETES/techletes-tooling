---
name: adopt-python-template
description: Use when an active Python or Techletes full-stack repository needs to adopt or update a Techletes template baseline. Establishes the correct upstream, performs first adoption, and configures a permanent chore/template-sync branch plus GitHub Actions so later template updates are merged safely without touching feature branches or cluttering staging history.
---

# Adopt a Techletes Python or Full-Stack Template

Bring an active Python or FastAPI/React repository onto the correct Techletes
template without rewriting its application. Generic tooling belongs to the
upstream template; the target owns its product code, dependencies, package
identity, frontend, deployment behavior, and domain documentation.

The supported hierarchy is:

```text
TECHLETES/python_template -> TECHLETES/full-stack-template -> full-stack project
```

`full-stack-template` itself follows `python_template`. A full-stack project
follows `full-stack-template`, not `python_template` directly.

The permanent update model is:

```text
template/main
      | real merge, ancestry retained
      v
chore/template-sync
      | squash PR
      v
staging
      | normal release merge
      v
main
```

Never merge template updates from a developer feature branch or from a
devcontainer startup hook.

## Use Only When

- The repository is active and Python-based or a Techletes full-stack project.
- No explicit client or product requirement mandates another baseline.
- A separate migration PR is acceptable for first adoption.

Stop and report instead of merging for archived repositories, temporary
scripts, non-Python/non-full-stack repositories, or unclear ownership of
production configuration.

## Choose the upstream before changing files

Classify the target and choose its immediate upstream before creating a branch:

| Target | Upstream remote `template` |
|---|---|
| Python-only repository | `git@github.com:TECHLETES/python_template.git` |
| `TECHLETES/full-stack-template` itself | `git@github.com:TECHLETES/python_template.git` |
| Full-stack project cloned from the full-stack template | `git@github.com:TECHLETES/full-stack-template.git` |

If the target type, intended parent, or existing `template` remote is unclear,
ask the user before merging. Inspect the frontend, compose/deployment files,
repository origin, and current branch model first.

**REQUIRED SUB-SKILL:** Use `techletes-superpowers:verification-before-completion`
before claiming adoption is complete. Use
`techletes-superpowers:systematic-debugging` for merge, install, hook, workflow,
or test failures rather than bypassing them.

## Preflight

1. Read the target repository's `AGENTS.md`, `README.md`, `pyproject.toml`, CI
   workflows, devcontainer files, branch rules, and—for full-stack targets—
   frontend manifests and compose/deployment files.
2. Identify the integration branch. Prefer `staging`; if the repository uses a
   different development branch, record that branch and use it consistently.
3. Require a clean working tree. Do not stash, reset, or discard user work.
4. Inspect whether template-merging logic currently exists in
   `.devcontainer/post-attach.sh`, `post-create.sh`, or other local startup
   scripts. Plan to remove it; startup hooks may start services but must not
   fetch, merge, stage, commit, or modify Git history.
5. Check whether `chore/template-sync`, `.template-sync.yml`, or a template-sync
   workflow already exists. Preserve and update an existing valid setup rather
   than recreating it.
6. Record the starting branch and commit so the migration can be abandoned
   safely without destructive Git commands.

## First Adoption

Use a temporary adoption branch from the integration branch:

```bash
git fetch origin
git switch staging
git pull --ff-only origin staging
git switch -c chore/adopt-template
```

Replace `staging` when the repository uses another integration branch.

Configure the immediate upstream idempotently:

```bash
expected_template_url='git@github.com:TECHLETES/python_template.git'  # choose first
configured_template_url="$(git remote get-url template 2>/dev/null || true)"

if [ -z "$configured_template_url" ]; then
  git remote add template "$expected_template_url"
  git remote set-url --push template DISABLED
elif [ "$configured_template_url" != "$expected_template_url" ]; then
  echo "template remote points to an unexpected URL: $configured_template_url" >&2
  exit 1
fi

git fetch template main
```

Perform the first real merge and retain template ancestry:

```bash
git merge template/main --allow-unrelated-histories --no-commit --no-ff
```

Do not commit until conflicts are resolved and the merged tree is inspected.
Run the template's existing adoption helper after the merge. Prefer discovered
project metadata; pass explicit values when inference would be wrong:

```bash
uv run python scripts/adopt-template.py \
  --name my-repository \
  --package my_package \
  --description "Short project description."
```

Do not invent a second migration script or manually copy the complete template.
For a full-stack target, do not import Python-template sample application code
or generic package directories. Keep the target's backend, frontend, generated
client, and service layout.

After resolving and verifying the first adoption, commit it on
`chore/adopt-template` and open a PR to the integration branch. A squash merge is
acceptable for this one-time migration.

## Conflict Ownership

| Area | Decision |
|---|---|
| Application code, migrations, domain docs | Keep target repository |
| Full-stack backend/frontend, generated client, compose, Caddy, deployment | Keep target repository; merge generic tooling around them |
| Existing dependencies and package name | Keep target repository; merge only required template tooling |
| `.devcontainer/`, pre-commit, VS Code settings, generic docs | Prefer template, then adapt project-specific paths, services, ports, and upstream URL |
| `pyproject.toml` | Merge metadata and dependencies carefully; take template tool configuration without deleting target settings |
| `uv.lock` | Never hand-merge; regenerate with `uv lock` after `pyproject.toml` is final |
| Frontend `package.json`, lockfile, build and test config | Keep target repository; preserve its toolchain and service conventions |
| Deployment and release workflows | Preserve; add compatible quality jobs without removing triggers, secrets, or release steps |
| `.envrc`, `.env.template`, client config | Preserve variables and semantics; add only documented generic entries |
| `README.md`, `AGENTS.md` | Preserve project context and add the new setup/quality workflow |
| `.secret.baseline` | Re-scan using the configured tool; investigate every new finding |

When a conflict cannot be classified from the repository, stop before choosing
the template version. A successful merge is not evidence that the result is
safe.

## Configure Permanent Template Synchronization

First adoption is incomplete until the repository has a permanent sync branch,
allowlist, and GitHub Actions workflow.

### 1. Create `.template-sync.yml`

Create a target-owned allowlist. Do not use an ignore-list because newly added
application files in the template must not propagate automatically.

```yaml
source:
  repository: TECHLETES/full-stack-template
  branch: main

target:
  branch: staging
  sync_branch: chore/template-sync

paths:
  - .devcontainer/**
  - .github/workflows/**
  - .pre-commit-config.yaml
  - .python-version
  - biome.json
  - pyproject.toml
```

Choose `TECHLETES/python_template` for Python-only targets and for
`full-stack-template` itself. Adapt `target.branch` to the repository's actual
integration branch.

Start conservatively. Include only files that should remain aligned with the
upstream. Mixed-ownership files such as `pyproject.toml`, `package.json`,
`README.md`, `AGENTS.md`, compose files, and deployment workflows require
explicit review and may be excluded initially.

The sync config is target-owned and must not itself be synchronized.

### 2. Create the permanent sync branch

Create `chore/template-sync` from the adopted integration branch after the
first-adoption PR is merged:

```bash
git fetch origin
git switch staging
git pull --ff-only origin staging
git switch -c chore/template-sync
git push -u origin chore/template-sync
```

This branch is permanent. Never delete, recreate, rebase, reset, or force-push
it. Its retained merge ancestry is what tells Git which template commits were
already processed.

Configure a branch ruleset matching exactly `chore/template-sync`:

- enable **Restrict deletions**;
- enable **Block force pushes**;
- do not require linear history;
- do not require pull requests for updates to this branch;
- normally leave status checks on the PR into `staging`, not on direct sync
  branch updates;
- ensure the template-sync GitHub App or automation identity can update it;
- retain a restricted maintainer/admin bypass for recovery.

### 3. Add the reusable or local GitHub Actions workflow

Prefer a reusable workflow maintained centrally by Techletes. The target repo
should contain only a small caller with `workflow_dispatch` and a schedule.
When a central reusable workflow is unavailable, implement the same behavior in
a local workflow.

The workflow must:

1. Check out `chore/template-sync` with full history.
2. Fetch the integration branch and the configured `template/main`.
3. Merge the latest integration branch into `chore/template-sync`.
4. Merge `template/main` with a real merge commit.
5. Keep only paths listed in `.template-sync.yml`.
6. Restore unmanaged paths to the pre-template-merge target version.
7. Automatically resolve unmanaged conflicts in favor of the target.
8. Leave managed conflicts unresolved and fail with clear instructions.
9. Commit and push the sync branch only when the managed merge is clean.
10. Open or update one PR from `chore/template-sync` to the integration branch.

The PR must be squash-merged. Do not delete the head branch after merging.

The workflow must never merge or push directly to `staging` or `main`.

### 4. Preserve ancestry while filtering paths

Filtering paths must not be implemented as simple file replacement. The
workflow must first perform a normal Git merge from `template/main`, then restore
all paths outside the allowlist before committing. The resulting commit must
retain both parents:

```text
previous chore/template-sync commit
configured template/main commit
```

This records the template commits as processed while limiting the resulting
content to approved paths.

### 5. Authentication

For private repositories, prefer a Techletes GitHub App with:

- read access to the template repository;
- contents and pull-request write access to target repositories;
- workflow write access only when synchronized workflow files require it.

Do not use a developer's personal token when an organization-owned App is
available. Never commit tokens or place long-lived credentials in repository
files.

## Later Template Updates

All later updates use only the permanent branch and workflow.

Never create `chore/update-template` branches and never merge template updates
from feature branches, `post-attach.sh`, or `post-create.sh`.

Expected automated sequence:

```text
checkout chore/template-sync
merge origin/staging
merge template/main
filter to configured paths
push chore/template-sync
open or update PR to staging
```

After the PR is squash-merged, the next workflow run merges the updated
integration branch back into `chore/template-sync`. This keeps the branches
close while preserving template ancestry on the sync branch.

When managed files conflict, the workflow must fail without pushing an
unresolved merge. A developer resolves it locally:

```bash
git fetch origin
git switch chore/template-sync
git pull --ff-only origin chore/template-sync
git fetch template main
git merge origin/staging
git merge template/main
# resolve only the reported managed conflicts
git add <resolved-files>
git commit
git push origin chore/template-sync
```

Adapt `staging` and the template remote to the repository configuration. Do not
abort, reset, rebase, or recreate the branch merely to avoid a conflict.

## Remove Legacy Startup Merging

Remove template-fetch and template-merge logic from devcontainer startup
scripts. A valid `post-attach.sh` may start or restart services only, for example:

```bash
#!/bin/bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${repo_root}"

bash .devcontainer/dev-services.sh restart
```

Opening a devcontainer must never modify Git state.

## Finish and Verify

After resolving first adoption or a manual sync conflict, run the repository's
documented checks. Typical Python checks are:

```bash
git diff --check
uv lock
uv sync
uv run pre-commit install --install-hooks
uv run pre-commit run --all-files
uv run pytest
```

For full-stack targets, also run the smallest documented frontend checks, such
as lint, type checking, and tests. Regenerate the frontend client only when API
changes require it. Follow the target's `AGENTS.md` for Docker restrictions.

Verify the synchronization setup itself:

- `.template-sync.yml` points to the correct immediate upstream and integration
  branch;
- `chore/template-sync` exists remotely and contains the required ancestry;
- the ruleset blocks deletion and force pushes but permits merge commits;
- the workflow has an explicit schedule and manual trigger;
- the workflow cannot push directly to `staging` or `main`;
- the sync PR uses `chore/template-sync` as head and the integration branch as
  base;
- automatic branch deletion is not applied to the permanent sync branch;
- legacy devcontainer merge logic is gone;
- existing deployment workflows remain present;
- no real secrets entered the repository or secret baseline.

## Completion Evidence

The adoption PR must state:

- selected immediate upstream and template commit merged;
- target integration branch;
- metadata/package choices and files intentionally preserved;
- `.template-sync.yml` paths and exclusions;
- permanent sync branch creation status;
- branch ruleset status;
- workflow location, schedule, and authentication method;
- validation results, including frontend checks when applicable;
- devcontainer result or documented reason it was not run;
- secret baseline result and any legacy gaps.

Do not claim completion when the code was adopted but the permanent sync branch,
ruleset, workflow, or removal of startup merging is still missing.
