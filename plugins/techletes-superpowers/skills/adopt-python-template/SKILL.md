---
name: adopt-python-template
description: Use when an active Python or Techletes full-stack repository needs to adopt or update a Techletes template baseline. Establishes the correct upstream and configures the permanent template-sync branch, reusable GitHub Actions caller, first synchronization PR, local or reusable reconciliation, and retained ancestry.
---

# Adopt a Techletes Python or Full-Stack Template

Bring an active Python or FastAPI/React repository onto the correct Techletes
template without replacing application-specific behavior.

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
      | post-merge reconciliation
      v
chore/template-sync
```

Never merge template updates from a developer feature branch or a devcontainer
startup hook.

## Required sub-skills

Use `techletes-superpowers:verification-before-completion` before claiming
adoption is complete. Use `techletes-superpowers:systematic-debugging` for
merge, workflow, install, hook, or test failures rather than bypassing them.

## Four distinct phases

Keep these phases separate in both execution and reporting:

1. **Setup PR** — add target-owned configuration and workflow files.
2. **Permanent branch creation** — create `chore/template-sync` from the current
   integration branch.
3. **First sync PR** — run the template merge and review the resulting PR.
4. **Post-merge reconciliation** — merge the squash result back into the
   permanent branch.

Do not collapse these into one opaque migration step.

## Choose the immediate upstream

| Target | Immediate upstream |
|---|---|
| Python-only repository | `TECHLETES/python_template` |
| `TECHLETES/full-stack-template` itself | `TECHLETES/python_template` |
| Full-stack project | `TECHLETES/full-stack-template` |

If the target type or intended parent is unclear, inspect the repository origin,
frontend, compose/deployment files, and branch model, then ask before continuing.

## Preflight

1. Read `AGENTS.md`, `README.md`, `pyproject.toml`, CI workflows, devcontainer
   files, branch rules, and—for full-stack targets—frontend and deployment files.
2. Determine both the integration branch, normally `staging`, and the repository
   default branch, commonly `main`.
3. Require a clean working tree. Do not stash, reset, or discard user work.
4. Check whether `.template-sync.yml`, `chore/template-sync`, or either workflow
   already exists. Preserve and repair a valid setup rather than recreating it.
5. Inspect devcontainer startup scripts for template-fetch or template-merge
   logic. Remove such logic; opening a devcontainer must not modify Git history.
6. Inspect whether CI or bots can push generated files, such as coverage badges,
   to `chore/template-sync`. Record this because reconciliation must fetch and
   preserve remote-only commits.
7. Record the starting branch and commit.

## Canonical managed-path rule

Do not invent a shortened allowlist from memory or from examples in this skill.

The immediate upstream template's own downstream `.template-sync.yml` is the
canonical baseline for managed paths:

- A full-stack project following `TECHLETES/full-stack-template` must fetch
  `TECHLETES/full-stack-template/main:.template-sync.yml` and copy its complete
  current `paths` list.
- A Python-only project following `TECHLETES/python_template` must fetch the
  current Python downstream baseline designated by that repository.
- `TECHLETES/full-stack-template` following `python_template` uses its dedicated
  `.python-template-sync.yml`, not its downstream `.template-sync.yml`.

Copy the canonical `paths` list programmatically or verbatim from the live file.
Do not reconstruct it by hand. Then make only deliberate, documented exclusions
where the target truly owns a path.

Never omit an entry merely because the target does not yet contain that file;
one purpose of synchronization is to receive new governed files later.

The target repository's `.template-sync.yml` is always target-owned and must
never appear in its own `paths` list.

## Retroactive path warning

Adding a path to `.template-sync.yml` after the corresponding template commit is
already an ancestor of `chore/template-sync` does **not** retroactively copy that
historical file content. The workflow correctly considers that template commit
already processed.

Before expanding `paths`, check whether the desired upstream file state is
already behind the recorded template merge commit.

When retroactive adoption is required, use one of these explicit remedies:

1. Prefer a new upstream commit that touches the newly managed files, then run
   template sync normally.
2. Otherwise perform a one-time manual reconciliation on
   `chore/template-sync`: fetch the live upstream file versions, copy or merge
   them into the target, commit, and push without rewriting ancestry.

Do not expect a config-only allowlist change to replay historical template
content.

## Conflict ownership

Use these rules only for documented exclusions or PR reconciliation. They do not
replace the canonical upstream allowlist.

| Area | Decision |
|---|---|
| Application code, migrations, domain-specific docs | Target-owned |
| Existing dependencies and package identity | Target-owned; merge tooling carefully |
| Centrally governed quality and engineering files | Template-managed, then adapt target-specific values |
| `pyproject.toml` | Mixed content; reconcile rather than silently exclude when governed upstream |
| `uv.lock` | Never hand-merge; regenerate after `pyproject.toml` is final |
| Product-specific release/deployment behavior | Preserve unless explicitly governed upstream |
| `.secret.baseline` | Regenerate with configured tooling and investigate findings |

### Devcontainer caution

Treat `.devcontainer/**` as a warning-level convenience, not an automatic safe
choice. Safety-critical or environment-specific hooks—especially
`post-attach.sh`, `post-create.sh`, `initialize.sh`, service startup scripts,
mount configuration, ports, and credentials wiring—must be reviewed against the
**current live upstream file** before they are managed.

Keep a hook target-owned when the upstream version has not been verified safe
for the target repository. Never allow a synchronized hook to fetch templates,
merge branches, stage files, commit, or push.

# Phase 1: Setup PR

## 1. Create `.template-sync.yml`

Fetch the immediate upstream's live canonical downstream configuration. Copy its
complete `paths` list, then set only target-specific source and branch values.

Typical full-stack project header:

```yaml
source:
  repository: TECHLETES/full-stack-template
  branch: main

target:
  branch: staging
  sync_branch: chore/template-sync

paths:
  # Copy the complete current paths list verbatim from
  # TECHLETES/full-stack-template/main:.template-sync.yml.
```

Validation before committing:

- `source.repository` is the immediate upstream;
- `target.branch` is the actual integration branch;
- `target.sync_branch` is `chore/template-sync`;
- every canonical upstream path is present unless explicitly excluded;
- `.template-sync.yml` itself is absent from `paths`;
- sensitive devcontainer hooks were reviewed individually.

## 2. Add the reusable template-sync caller

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

For Python-only targets, set `template_repository` to
`TECHLETES/python_template`. The reusable sync implementation is currently
provided by `python_template`.

Caller inputs must exactly match `.template-sync.yml`.

## 3. Add post-merge reconciliation

First inspect the live central repository before choosing the implementation:

- `python_template` currently provides the reusable template-sync workflow.
- Do **not** assume it also provides
  `.github/workflows/reusable-reconcile-template-sync-branch.yml`.
- Only use a reusable `uses:` reference after verifying that exact workflow file
  exists on the referenced branch.

If a reusable reconciliation workflow exists, add a small local caller.
Otherwise add a complete local reconciliation workflow in the target repository.
A local implementation is explicitly supported and preferred over an invalid
central reference.

The reconciliation workflow must:

1. Trigger on a merged PR into the integration branch whose head is exactly
   `chore/template-sync` and whose head repository is the current repository.
2. Check out `chore/template-sync` with full history.
3. Fetch both `origin/chore/template-sync` and the integration branch.
4. Fast-forward or reset only the local checkout to the fetched remote sync
   branch before doing work; never rewrite the remote branch.
5. Merge the integration branch with `--no-ff`.
6. Push normally; never force-push.
7. Fail clearly and list conflicts when manual resolution is required.

When CI or bots may have added remote-only commits, always run:

```bash
git fetch origin
git switch chore/template-sync
git pull --ff-only origin chore/template-sync
```

before creating or pushing a reconciliation commit. This preserves generated
badge commits and other automation changes.

## 4. Bootstrap through the default branch

The setup PR contains:

```text
.template-sync.yml
.github/workflows/template-sync.yml
.github/workflows/reconcile-template-sync-branch.yml
```

Merge it into the integration branch first.

If the default branch differs from the integration branch—for example, `main`
is default and `staging` is integration—promote the setup through the normal
`staging -> main` release PR before attempting the first workflow run.

The workflow files must exist on the default branch because manual and scheduled
workflows are discovered there and the PR event listener must be installed
there.

# Phase 2: Permanent branch creation

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

Never seed it with copied template files, an orphan commit, or a manual upstream
merge. Never delete, recreate, rebase, reset, or force-push the remote branch.

## Create or verify the permanent-branch ruleset

Use GitHub CLI/API rather than relying only on a visual check.

Inspect existing rulesets:

```bash
gh api --paginate \
  "/repos/${GITHUB_REPOSITORY}/rulesets" \
  --jq '.[] | {id, name, enforcement, conditions, rules}'
```

Verify there is an active branch ruleset whose include pattern matches exactly:

```text
refs/heads/chore/template-sync
```

It must block deletion and non-fast-forward/force-push updates, permit merge
commits, permit direct automation updates, and retain an appropriate restricted
bypass actor.

If no suitable ruleset exists, create one through the repository rulesets API.
Use a JSON file so the payload is reviewable:

```bash
cat > /tmp/template-sync-ruleset.json <<'JSON'
{
  "name": "Protect permanent template sync branch",
  "target": "branch",
  "enforcement": "active",
  "conditions": {
    "ref_name": {
      "include": ["refs/heads/chore/template-sync"],
      "exclude": []
    }
  },
  "rules": [
    {"type": "deletion"},
    {"type": "non_fast_forward"}
  ],
  "bypass_actors": []
}
JSON

gh api \
  --method POST \
  "/repos/${GITHUB_REPOSITORY}/rulesets" \
  --input /tmp/template-sync-ruleset.json
```

Before creating it, inspect organization policy and existing bypass actors. Add
the approved GitHub App or maintainer bypass configuration rather than guessing
actor IDs. Do not create duplicate overlapping rulesets.

# Phase 3: First sync PR

Immediately before the first sync, fetch and inspect again:

- the live upstream `.template-sync.yml`;
- the live upstream versions of safety-critical managed files;
- the exact reusable workflow files referenced by `uses:`.

This protects against changes between the setup PR and first execution.

Trigger the template-sync caller manually.

The reusable workflow must:

1. Check out `chore/template-sync` with full history.
2. Fetch the integration branch and configured immediate upstream.
3. Merge the integration branch into the permanent sync branch.
4. Merge the upstream branch with `--allow-unrelated-histories`, retaining a
   genuine two-parent merge commit.
5. Restore paths outside the allowlist to their pre-template state.
6. Resolve unmanaged conflicts in favor of the target.
7. Apply the template version for managed conflicts so proposed upstream content
   appears in the PR diff.
8. Push the permanent branch.
9. Open or update one PR to the integration branch.
10. Open the PR as draft when managed conflicts require review.

The workflow must never push directly to the integration or default branch.

## Review the first sync PR

Before reconciliation, fetch the live upstream files again. Do not assume the
versions reviewed during setup are still current.

For managed conflicts, review the listed files under **Files changed** and
restore only required target-specific behavior on the permanent branch:

```bash
git fetch origin
git switch chore/template-sync
git pull --ff-only origin chore/template-sync

# Fetch and inspect the current upstream file versions before editing.
# Edit and test the listed files.

git add <reconciled-files>
git commit -m "chore: reconcile template conflicts"
git push origin chore/template-sync
```

Then validate, remove the manual-reconciliation marker from the PR body, mark it
ready, squash-merge it, and do not delete `chore/template-sync`.

# Phase 4: Post-merge reconciliation

After the squash merge, reconciliation must merge the updated integration branch
back into `chore/template-sync`.

Expected final relationship:

```text
integration branch is an ancestor of chore/template-sync
upstream template/main is an ancestor of chore/template-sync
```

If reconciliation conflicts, resolve once on the permanent branch:

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

Never force-push. If the normal push is rejected, fetch again and incorporate the
new remote commits before retrying.

## Later template updates

All future updates use the permanent branch and sync/reconciliation workflows:

```text
checkout chore/template-sync
fetch and incorporate remote-only commits
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
- the target `paths` list was copied from the live canonical upstream file;
- any deviations are explicitly documented;
- `.template-sync.yml` does not list itself;
- safety-critical devcontainer hooks were individually reviewed;
- workflow files exist on both integration and default branches when those
  branches differ;
- every referenced reusable workflow exists at the referenced ref;
- local reconciliation is used when no reusable implementation exists;
- `chore/template-sync` was created from the current integration branch;
- the permanent-branch ruleset was verified through GitHub CLI/API;
- the first sync retained upstream ancestry;
- no expected historical content was missed because of a retroactively expanded
  allowlist;
- managed conflicts are visible in the draft PR diff;
- remote-only CI/bot commits were preserved;
- the PR was squash-merged without deleting the permanent branch;
- post-merge reconciliation succeeded;
- legacy devcontainer merge logic is gone;
- existing product-specific behavior and deployment workflows remain intact.

Do not claim completion when canonical path comparison, workflow bootstrap,
permanent branch protection, first sync PR, retroactive path handling, required
reconciliation, or validation is missing.
