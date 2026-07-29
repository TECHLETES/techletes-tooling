---
name: adopt-python-template
description: Use when an active Python or Techletes full-stack repository needs to adopt, repair, or update Techletes template synchronization. Determines the correct upstream, preserves partial valid setup, configures the permanent sync branch and workflows, and retains template ancestry.
---

# Adopt a Techletes Python or Full-Stack Template

Use this skill to set up or repair template synchronization without replacing
application-specific behavior.

Supported hierarchy:

```text
TECHLETES/python_template -> TECHLETES/full-stack-template -> full-stack project
```

- Python-only repositories follow `TECHLETES/python_template`.
- `TECHLETES/full-stack-template` itself follows `TECHLETES/python_template`.
- Normal full-stack projects follow `TECHLETES/full-stack-template`.

Never merge template updates from a developer feature branch or a devcontainer
startup hook.

## Required sub-skills

Use `techletes-superpowers:verification-before-completion` before claiming the
setup is complete. Use `techletes-superpowers:systematic-debugging` for workflow,
merge, hook, installation, or test failures.

## Four distinct phases

Keep these phases separate:

1. **Setup PR** — add or repair target-owned configuration and workflow files.
2. **Permanent branch creation** — create the permanent sync branch from the
   current integration branch.
3. **First sync PR** — run template synchronization and review the resulting PR.
4. **Post-merge reconciliation** — merge the updated integration branch back
   into the permanent sync branch.

For a partially implemented repository, inspect the existing state and continue
from the first incomplete phase. Preserve valid existing components. Never
restart by deleting or rewriting the permanent branch.

## Determine repository branches and upstream

Before changing files, determine:

- the immediate upstream template;
- whether a `staging` branch exists;
- the integration branch, which is **always `staging` when that branch exists,
  otherwise `main`**;
- the repository default branch, commonly `main`;
- whether the repository already contains sync configuration, workflows, a
  permanent branch, or an open sync PR.

Do not infer the integration branch from the default branch. A repository may
have `main` as default while still using `staging` as its integration branch.

| Target | Immediate upstream | Config source |
|---|---|---|
| Python-only repository | `TECHLETES/python_template` | upstream `.template-sync.yml` |
| `TECHLETES/full-stack-template` itself | `TECHLETES/python_template` | `.python-template-sync.yml` |
| Full-stack project | `TECHLETES/full-stack-template` | upstream `.template-sync.yml` |

If the repository type is unclear, inspect its origin, frontend, compose and
deployment files before proceeding.

# Phase 1: Setup PR

## Exact sync-configuration rule

The direct upstream configuration is canonical. Fetch the live configuration
from the upstream default branch immediately before creating or repairing the
target configuration.

For a normal downstream repository:

1. Copy the upstream `.template-sync.yml` file **verbatim**.
2. Change **only** `target.branch` to the current repository's actual integration
   branch: `staging` when it exists, otherwise `main`.
3. Do not add, remove, reorder, rename, or rewrite any `paths` entry.
4. Do not change `source.repository`, `source.branch`, or
   `target.sync_branch` unless this skill's repository hierarchy explicitly
   requires another upstream or permanent branch.
5. Do not rewrite comments or reconstruct the list manually.

For `TECHLETES/full-stack-template` following `python_template`, copy its
canonical `.python-template-sync.yml` in the same way and change only the target
branch when required.

Required invariant:

```text
target paths == upstream canonical paths
```

There are **no downstream path exclusions**. Project-specific behavior in a
managed file is preserved by reconciling that file's contents in the sync PR,
not by removing the file from `paths`.

Keep managed:

- `.github/workflows/template-sync.yml`, even when the downstream repository
  targets `main` and the upstream example targets `staging`;
- `.devcontainer/**`, even when downstream hooks contain extra setup;
- mixed-content files such as `pyproject.toml` when present in the canonical list.

The configuration file must never list itself. If the canonical upstream config
contains its own config path, a nonexistent managed file, or another structural
error, stop and fix the upstream template rather than creating downstream
divergence.

## Add or repair the template-sync caller

Use the central sync engine:

```yaml
uses: TECHLETES/python_template/.github/workflows/reusable-template-sync.yml@main
```

Caller inputs must exactly match the target configuration:

```yaml
with:
  template_repository: <source.repository>
  template_branch: <source.branch>
  target_branch: <target.branch>
  sync_branch: <target.sync_branch>
  config_path: .template-sync.yml
```

Use `TECHLETES/full-stack-template` as `template_repository` for a normal
full-stack project. Do not duplicate the reusable sync engine locally.

## Organization-provided credentials

The following Actions values are provided centrally at the TECHLETES
organization level and are available to participating repositories:

```text
TEMPLATE_SYNC_APP_CLIENT_ID
TEMPLATE_SYNC_APP_PRIVATE_KEY
```

Assume these values are available. Do not block Phase 2 or Phase 3, ask the user
to configure repository-level values, or report them as missing merely because
repository-level variable or secret listings are empty. Organization-level
secrets are intentionally not readable through normal repository inspection.

Proceed with creating the permanent branch and triggering the first sync. Only
treat credentials as unavailable when an actual workflow run fails with an
explicit credential, secret-access, or GitHub App token error. Diagnose that
concrete run failure instead of pre-emptively stopping.

## Add or repair reconciliation

First verify whether the exact reusable reconciliation workflow referenced by a
caller exists on the referenced branch. Never create a `uses:` reference to a
nonexistent workflow.

When no reusable reconciliation workflow exists, add a complete local workflow.

The reconciliation workflow must **always** trigger on every push to the actual
integration branch. Resolve that branch first using this exact rule:

```text
integration branch = staging if the repository has a staging branch, else main
```

Then write the trigger with the resolved literal branch name. For example, when
`staging` exists:

```yaml
name: Reconcile template sync branch

on:
  push:
    branches:
      - staging
```

For a repository without `staging`:

```yaml
name: Reconcile template sync branch

on:
  push:
    branches:
      - main
```

Never leave `<integration-branch>` as a placeholder, never default this trigger
to the repository default branch, and never use `main` when `staging` exists.
The reconciliation trigger branch must exactly equal both:

- `.template-sync.yml` -> `target.branch`;
- `.github/workflows/template-sync.yml` -> `with.target_branch`.

A push trigger covers normal PR merges, the squash merge of the template-sync
PR, and permitted direct pushes. The reconciliation workflow must:

1. Check out the permanent sync branch with full history.
2. Fetch the remote permanent branch and resolved integration branch.
3. Ensure the local checkout matches the remote permanent branch.
4. Exit successfully when the integration branch is already an ancestor.
5. Merge the integration branch with `--no-ff`.
6. Push normally without force-pushing.
7. Fail clearly and list conflicts when manual resolution is needed.

Use concurrency with `cancel-in-progress: false` so closely spaced integration
branch pushes queue rather than interrupting one another.

## Remove legacy startup merging

Remove any template fetch, merge, staging, commit, or push behavior from
`post-create.sh`, `post-attach.sh`, or other devcontainer startup hooks. Opening a
devcontainer must never modify Git history.

## Open and label the setup PR

Open the Phase 1 setup PR through the repository's normal contribution flow.
Add the existing `chore` label to this initial setup PR. If the repository does
not yet have a `chore` label, create it before labeling the PR.

```bash
gh label create chore --description "Maintenance and repository tooling" --color BFD4F2 2>/dev/null || true
gh pr edit <setup-pr-number> --add-label chore
```

Do not apply a substitute label when `chore` is absent.

## Bootstrap through the default branch

The setup PR contains the configuration and local workflow files.

When the default branch differs from the integration branch—for example, `main`
is default and `staging` is integration—promote the setup through the normal
`staging -> main` flow before attempting the first workflow run.

Manual and scheduled workflows must exist on the default branch. Their target
and the reconciliation push trigger must still use the resolved integration
branch.

# Phase 2: Permanent branch creation

Create the permanent branch directly from the latest integration branch:

```bash
git fetch origin
git switch <integration-branch>
git pull --ff-only origin <integration-branch>
git switch -c chore/template-sync
git push -u origin chore/template-sync
```

Initial invariant:

```text
chore/template-sync == integration branch
```

Never seed it with copied template files, an orphan commit, or a manual upstream
merge. Never delete, recreate, rebase, reset, or force-push the remote permanent
branch.

Create or verify a ruleset matching exactly:

```text
refs/heads/chore/template-sync
```

It must block deletion and non-fast-forward updates while allowing normal merge
commits and direct automation updates. Inspect existing repository and
organization rules before creating a new ruleset; do not create duplicates or
guess bypass actor IDs.

# Phase 3: First sync PR

Immediately before the first run, fetch and inspect again:

- the live upstream configuration;
- the exact reusable workflow referenced by the caller;
- the live upstream versions of managed files.

Verify exact configuration equality except for the permitted target-branch
change.

Do not perform a repository-level preflight check for
`TEMPLATE_SYNC_APP_CLIENT_ID` or `TEMPLATE_SYNC_APP_PRIVATE_KEY`. They are
organization-provided. Trigger the workflow and use the run result as the source
of truth for credential availability.

Trigger the template-sync caller manually. The sync engine must:

1. Check out the permanent branch with full history.
2. Merge the current integration branch into it.
3. Merge the immediate upstream with real Git ancestry.
4. Retain only the canonical managed paths.
5. Apply upstream versions for managed conflicts so changes are visible in the
   PR diff.
6. Push the permanent branch.
7. Open or update one PR to the integration branch.
8. Use a draft PR when manual reconciliation is required.
9. Add the `chore` label to every template-sync PR, including the first and all
   later updated or newly opened sync PRs.

When the reusable sync workflow does not apply labels itself:

```bash
gh label create chore --description "Maintenance and repository tooling" --color BFD4F2 2>/dev/null || true
gh pr edit <sync-pr-number> --add-label chore
```

Do not consider PR creation complete until the `chore` label is present.
The workflow must never push directly to the integration or default branch.

## Review managed files

Review all managed changes under **Files changed**. Preserve required
repository-specific behavior in the managed file itself and commit the
reconciliation to the permanent branch.

Before any manual commit:

```bash
git fetch origin
git switch chore/template-sync
git pull --ff-only origin chore/template-sync
```

This preserves remote-only CI or bot commits. Never force-push.

Run the repository's documented validation, then squash-merge the sync PR.
Never delete the permanent branch.

# Phase 4: Post-merge reconciliation

Every push to the resolved integration branch must trigger reconciliation. This
includes the push caused by squash-merging the template-sync PR and pushes caused
by all other merged PRs or permitted direct changes.

The workflow merges the updated integration branch back into the permanent sync
branch.

Expected invariants:

```text
integration branch is an ancestor of chore/template-sync
upstream template commit is an ancestor of chore/template-sync
```

Resolve reconciliation conflicts on the permanent branch with a normal merge
commit. Never rebase, reset, recreate, or force-push it.

# Retroactive path behavior

Because downstream `paths` must equal the canonical upstream list from initial
setup, retroactive path adoption should normally not occur.

For an already-partial or previously incorrect setup, adding missing canonical
paths after the relevant upstream commit is already in permanent-branch ancestry
does not replay historical content.

Repair this by performing a one-time reconciliation on the permanent branch:
fetch the live upstream versions of all previously omitted canonical files,
merge or copy them into the permanent branch, preserve target-specific content,
commit normally, and open or update the sync PR. Do not rewrite ancestry.

# Verification

Before completion, verify:

- the correct immediate upstream was selected;
- the integration branch was resolved as `staging` when it exists, otherwise
  `main`;
- `.template-sync.yml`, the template-sync caller, and the reconciliation workflow
  all use that same integration branch;
- the reconciliation workflow uses `on.push.branches` with the resolved literal
  integration branch;
- the target configuration was copied from the live direct upstream;
- only `target.branch` differs from that canonical configuration, except for the
  special `full-stack-template`/`.python-template-sync.yml` relationship;
- the complete `paths` list is byte-for-byte equivalent in entries and order;
- no downstream exclusions exist;
- every reusable workflow reference exists;
- organization-provided template-sync credentials were assumed available unless
  an actual workflow run reported a concrete credential-access failure;
- setup workflows exist on the default branch;
- the permanent branch started from the current integration branch;
- deletion and force pushes are blocked;
- the initial setup PR has the `chore` label;
- the first and every later template-sync PR has the `chore` label;
- the first sync retained upstream ancestry;
- target-specific behavior was reconciled inside managed files;
- the sync PR was squash-merged without deleting the permanent branch;
- post-merge reconciliation succeeded;
- legacy devcontainer template merging is gone.

Do not claim completion while any of these checks remain unresolved.
