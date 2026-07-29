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
integration branch
      | merge back after squash
      v
chore/template-sync
```

Never merge template updates from a developer feature branch or from a
devcontainer startup hook.

## Required sub-skills

Use `techletes-superpowers:verification-before-completion` before claiming
adoption is complete. Use `techletes-superpowers:systematic-debugging` for
merge, workflow, install, hook, or test failures rather than bypassing them.

## Choose the immediate upstream

Classify the target before changing files:

| Target | Immediate upstream |
|---|---|
| Python-only repository | `TECHLETES/python_template` |
| `TECHLETES/full-stack-template` itself | `TECHLETES/python_template` |
| Full-stack project | `TECHLETES/full-stack-template` |

If the target type or intended parent is unclear, inspect the repository origin,
frontend, compose/deployment files, and branch model, then ask the user before
continuing.

## Preflight

1. Read `AGENTS.md`, `README.md`, `pyproject.toml`, CI workflows, devcontainer
   files, branch rules, and—for full-stack targets—frontend and deployment files.
2. Determine both:
   - the integration branch, normally `staging`;
   - the repository default branch, commonly `main`.
3. Require a clean working tree. Do not stash, reset, or discard user work.
4. Check whether `.template-sync.yml`, `chore/template-sync`, or either caller
   workflow already exists. Preserve and repair a valid setup rather than
   recreating it.
5. Inspect devcontainer startup scripts for template-fetch or template-merge
   logic. Remove such logic; opening a devcontainer must not modify Git history.
6. Record the starting branch and commit.

## Canonical managed-path rule

Do not invent a shortened allowlist from memory or from the example in this
skill.

The immediate upstream template's own downstream `.template-sync.yml` is the
canonical baseline for managed paths:

- A full-stack project following `TECHLETES/full-stack-template` must read
  `TECHLETES/full-stack-template/main:.template-sync.yml` and start with its
  complete `paths` list.
- A Python-only project following `TECHLETES/python_template` must use the
  current downstream baseline designated by `python_template`; inspect the
  repository rather than guessing.
- `TECHLETES/full-stack-template` following `python_template` uses its dedicated
  `.python-template-sync.yml`, not its downstream `.template-sync.yml`.

Copy the canonical `paths` list completely first. Then make only deliberate,
documented target-specific exclusions where the target truly owns a path.
Never silently omit entries because the file does not yet exist in the target;
a principal purpose of synchronization is to receive newly added governed
files later.

The target repository's `.template-sync.yml` is always target-owned and must
never appear in its own `paths` list.

For example, the full-stack downstream baseline currently governs shared GitHub
workflows, devcontainer files, Python and frontend baseline files, runtime and
deployment baseline files, shared scripts, `AGENTS.md`, and explicitly governed
documentation. Fetch the live upstream file before implementation; do not rely
on this prose as the file list.

## Conflict ownership

Use these rules only when deciding documented exclusions or reconciling a sync
PR. They do not replace the canonical upstream allowlist.

| Area | Decision |
|---|---|
| Application code, migrations, domain-specific docs | Target-owned |
| Existing dependencies and package identity | Target-owned; merge tooling carefully |
| Centrally governed devcontainer, quality and engineering files | Template-managed, then adapt project-specific values |
| `pyproject.toml` | Mixed content, but keep managed when the upstream baseline governs it; reconcile rather than silently exclude |
| `uv.lock` | Never hand-merge; regenerate after `pyproject.toml` is final |
| Product-specific release/deployment behavior | Preserve unless the upstream baseline explicitly governs the file |
| `.secret.baseline` | Regenerate with the configured tooling; investigate findings |

## Initial setup

The first adoption uses the same permanent synchronization mechanism as later
updates. Do not manually merge the complete upstream template on a temporary
feature branch.

### 1. Create `.template-sync.yml`

Fetch the immediate upstream's canonical downstream configuration. Copy its
complete `paths` list, then set only the target-specific source and branches.

Typical full-stack project header:

```yaml
source:
  repository: TECHLETES/full-stack-template
  branch: main

target:
  branch: staging
  sync_branch: chore/template-sync

paths:
  # Copy the complete current paths list from
  # TECHLETES/full-stack-template/main:.template-sync.yml.
```

Typical Python-only project header:

```yaml
source:
  repository: TECHLETES/python_template
  branch: main

target:
  branch: staging
  sync_branch: chore/template-sync

paths:
  # Copy the complete current Python downstream baseline.
```

Validation before committing:

- `source.repository` is the immediate upstream;
- `target.branch` is the actual integration branch;
- `target.sync_branch` is `chore/template-sync`;
- every canonical upstream path is present unless an exclusion is explicitly
  documented;
- `.template-sync.yml` itself is absent from `paths`.

### 2. Add the template-sync caller

Create `.github/workflows/template-sync.yml`:

```yaml
name: Sync template

on:
  workflow_dispatch:
  schedule:
    - cron: "7 3 * * 1"

jobs:
  sync:
    uses: TECHLETES/python_template/.github/workflows/reusable-template-sync.yml@main

    with:
      template_repository: TECHLETES/full-stack-template
      template_branch: main
      target_branch: staging
      sync_branch: chore/template-sync
      config_path: .template-sync.yml
      pull_request_title: "chore: sync full-stack template"

    secrets:
      app_client_id: ${{ vars.TEMPLATE_SYNC_APP_CLIENT_ID }}
      app_private_key: ${{ secrets.TEMPLATE_SYNC_APP_PRIVATE_KEY }}
```

For Python-only targets, change `template_repository` and the title to
`TECHLETES/python_template`. The reusable implementation remains centralized in
`python_template` unless Techletes explicitly changes that architecture.

Caller inputs must exactly match `.template-sync.yml`.

### 3. Add the reconciliation caller

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
      github.event.pull_request.head.repo.full_name == github.repository &&
      github.event.pull_request.head.ref == 'chore/template-sync'

    uses: TECHLETES/python_template/.github/workflows/reusable-reconcile-template-sync-branch.yml@main

    with:
      target_branch: staging
      sync_branch: chore/template-sync

    secrets:
      app_client_id: ${{ vars.TEMPLATE_SYNC_APP_CLIENT_ID }}
      app_private_key: ${{ secrets.TEMPLATE_SYNC_APP_PRIVATE_KEY }}
```

Adapt `staging` to the actual integration branch. The event listener must remain
local because the pull-request event occurs in the target repository.

### 4. Bootstrap through the default branch

Create a normal setup PR containing:

```text
.template-sync.yml
.github/workflows/template-sync.yml
.github/workflows/reconcile-template-sync-branch.yml
```

Merge it into the integration branch first.

If the default branch differs from the integration branch—for example,
`main` is default and `staging` is integration—promote the setup through the
repository's normal `staging -> main` release PR before attempting the first
workflow run.

The workflow files must exist on the default branch because:

- `workflow_dispatch` is discovered there;
- scheduled workflows run from there;
- the local pull-request reconciliation listener must be installed there.

The configuration may still target `staging`; workflow location and target
branch are separate concerns.

Do not create the permanent sync branch until the bootstrap files are merged
into the integration branch and the workflow callers are present on the default
branch.

### 5. Create the permanent sync branch

Create `chore/template-sync` directly from the current integration branch:

```bash
git fetch origin
git switch staging
git pull --ff-only origin staging
git switch -c chore/template-sync
git push -u origin chore/template-sync
```

The initial relationship must be:

```text
chore/template-sync == integration branch
```

Do not seed it with copied template files, an orphan commit, or a manual
upstream merge.

This branch is permanent. Never delete, recreate, rebase, reset, or force-push
it. Configure a ruleset that blocks deletion and force pushes, permits merge
commits and direct automation updates, and retains a restricted recovery bypass.

### 6. Run the first sync

Trigger the template-sync caller manually.

The reusable workflow must:

1. Check out `chore/template-sync` with full history.
2. Fetch the integration branch and configured immediate upstream.
3. Merge the integration branch into the permanent sync branch.
4. Merge the upstream branch with `--allow-unrelated-histories`, retaining a
   genuine two-parent merge commit.
5. Restore every path outside the allowlist to its pre-template state.
6. Resolve unmanaged conflicts in favor of the target.
7. Apply the template version for managed conflicts so the actual proposed
   upstream content appears in the PR diff.
8. Push the permanent sync branch.
9. Open or update one PR to the integration branch.
10. Open that PR as draft when managed conflicts require review.

The workflow must never push directly to the integration or default branch.

### 7. Review and squash-merge the sync PR

For managed conflicts, review the listed files under **Files changed** and
restore only required target-specific behavior directly on the permanent branch:

```bash
git fetch origin
git switch chore/template-sync
git pull --ff-only origin chore/template-sync

# Edit and test the listed files.

git add <reconciled-files>
git commit -m "chore: reconcile template conflicts"
git push origin chore/template-sync
```

Then:

1. Validate the repository.
2. Remove the manual-reconciliation section and hidden marker from the PR body.
3. Mark the PR ready.
4. Squash-merge it.
5. Do not delete `chore/template-sync`.

### 8. Verify post-merge reconciliation

After the squash merge, the local reconciliation caller must merge the updated
integration branch back into `chore/template-sync`.

Expected final relationship:

```text
integration branch is an ancestor of chore/template-sync
upstream template/main is an ancestor of chore/template-sync
```

If reconciliation conflicts, resolve the merge once on the permanent branch.
Do not rebase, reset, recreate, or force-push it.

## Later template updates

All future updates use the permanent branch and the two caller workflows:

```text
checkout chore/template-sync
merge current integration branch
merge new upstream template commit
filter to canonical configured paths
apply template versions for managed conflicts
push chore/template-sync
open or update draft/normal PR
squash-merge without deleting branch
merge integration branch back into chore/template-sync
```

Never create one-off update branches and never merge templates from devcontainer
startup scripts.

## Verification

Run the repository's documented checks. Typical Python checks are:

```bash
git diff --check
uv lock
uv sync
uv run pre-commit install --install-hooks
uv run pre-commit run --all-files
uv run pytest
```

For full-stack targets, also run documented frontend lint, type checking, and
tests.

Before completion, verify:

- the correct immediate upstream was selected;
- the target `paths` list was derived from the immediate upstream's current
  canonical downstream `.template-sync.yml`, not handcrafted;
- any deviations from that canonical list are explicitly documented;
- `.template-sync.yml` does not list itself;
- both caller workflows exist on the integration branch and default branch;
- `chore/template-sync` was created from the current integration branch;
- the first sync retained upstream ancestry;
- managed conflicts are visible in the draft PR diff;
- the PR was squash-merged without deleting the permanent branch;
- post-merge reconciliation succeeded;
- legacy devcontainer merge logic is gone;
- existing product-specific behavior and deployment workflows remain intact.

Do not claim completion when the canonical path comparison, workflow bootstrap,
permanent branch, first sync PR, required reconciliation, or validation is still
missing.
