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
- the integration branch, usually `staging` or `main`;
- the default branch, commonly `main`;
- whether the repository already contains sync configuration, workflows, a
  permanent branch, or an open sync PR.

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
   branch.
3. Do not add, remove, reorder, rename, or rewrite any `paths` entry.
4. Do not change `source.repository`, `source.branch`, or
   `target.sync_branch` unless this skill's repository hierarchy explicitly
   requires another upstream or permanent branch.
5. Do not rewrite comments or reconstruct the list manually.

For `TECHLETES/full-stack-template` following `python_template`, copy its
canonical `.python-template-sync.yml` in the same way and change only the target
branch when required.

The required downstream invariant is:

```text
target paths == upstream canonical paths
```

There are **no downstream path exclusions**. Project-specific behavior in a
managed file is preserved by reconciling that file's contents in the sync PR,
not by removing the file from `paths`.

Examples:

- Keep `.github/workflows/template-sync.yml` managed even when the downstream
  repository targets `main` and the upstream example targets `staging`.
- Keep `.devcontainer/**` managed even when downstream hooks contain additional
  environment setup.
- Keep mixed-content files such as `pyproject.toml` managed when they appear in
  the canonical list.

For those files, preserve required target-specific values while reviewing the
sync PR. Do not solve content differences by changing the allowlist.

The configuration file must never list itself. If the canonical upstream config
contains its own config path, a nonexistent managed file, or another structural
error, stop and fix the upstream template rather than creating downstream
divergence.

## Add or repair the template-sync caller

Use the central sync engine:

```yaml
uses: TECHLETES/python_template/.github/workflows/reusable-template-sync.yml@main
```

The caller inputs must exactly match the target configuration:

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

## Add or repair reconciliation

First verify whether the exact reusable reconciliation workflow referenced by a
caller exists on the referenced branch. Never create a `uses:` reference to a
nonexistent workflow.

When no reusable reconciliation workflow exists, add a complete local workflow.
The reconciliation workflow should trigger on every push to the integration
branch:

```yaml
on:
  push:
    branches:
      - <integration-branch>
```

This covers normal PR merges, the squash merge of the template-sync PR, and any
permitted direct push. It must:

1. Check out the permanent sync branch with full history.
2. Fetch the remote permanent branch and integration branch.
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

## Bootstrap through the default branch

The setup PR contains the configuration and local workflow files.

When the default branch differs from the integration branch—for example,
`main` is default and `staging` is integration—promote the setup through the
normal `staging -> main` flow before attempting the first workflow run.

Manual and scheduled workflows must exist on the default branch. The workflow
configuration may still target the integration branch.

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

The integration-branch push caused by the squash merge must trigger the
reconciliation workflow. It merges the updated integration branch back into the
permanent sync branch.

Expected final invariants:

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
commit normally, and open/update the sync PR. Do not rewrite ancestry.

# Verification

Before completion, verify:

- the correct immediate upstream was selected;
- the target configuration was copied from the live direct upstream;
- only `target.branch` differs from that canonical configuration, except for the
  special `full-stack-template`/`.python-template-sync.yml` relationship;
- the complete `paths` list is byte-for-byte equivalent in entries and order;
- no downstream exclusions exist;
- the caller inputs match the configuration;
- every reusable workflow reference exists;
- local reconciliation triggers on every integration-branch push;
- setup workflows exist on the default branch;
- the permanent branch started from the current integration branch;
- deletion and force pushes are blocked;
- the first sync retained upstream ancestry;
- target-specific behavior was reconciled inside managed files;
- the sync PR was squash-merged without deleting the permanent branch;
- post-merge reconciliation succeeded;
- legacy devcontainer template merging is gone.

Do not claim completion while any of these checks remain unresolved.
