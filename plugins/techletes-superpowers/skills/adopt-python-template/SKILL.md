---
name: adopt-python-template
description: Use when Codex must make an active Python, FastAPI/React, or Techletes full-stack repository compliant with the current Techletes template architecture in one pass. Audit the repository, choose the immediate upstream, perform or repair the initial template merge on the permanent sync branch, install the target-owned allowlist and small reusable-workflow caller, remove legacy devcontainer merge logic, attempt repository ruleset configuration, run validation, and open or update the squash-merge PR without replacing project-specific application behavior.
---

# Adopt a Techletes Template End to End

Make the repository template compliant in one execution. Do not stop after copying
files or writing instructions when the available GitHub and shell access can
complete the work.

The supported hierarchy is:

```text
TECHLETES/python_template
        |
        +--> Python projects
        |
        +--> TECHLETES/full-stack-template
                    |
                    +--> Full-stack projects
```

The reusable synchronization engine lives only at:

```text
TECHLETES/python_template/.github/workflows/reusable-template-sync.yml@main
```

Targets contain only a small caller workflow and a target-owned sync config.

**REQUIRED SUB-SKILL:** Use
`techletes-superpowers:verification-before-completion` before claiming the
repository is compliant. Use `techletes-superpowers:systematic-debugging` for
merge, workflow, install, or test failures instead of bypassing them.

## Non-negotiable rules

- Use the permanent sync branch for first adoption and all later updates.
- Never create a disposable `chore/update-template` branch.
- Never delete, recreate, rebase, reset, or force-push a permanent sync branch.
- Never merge template changes from a feature branch or devcontainer hook.
- Never push template changes directly to `staging` or `main`.
- Never create a repository-local copy of the reusable synchronization engine.
- Never replace application code, dependencies, deployment behavior, or project
  context blindly. Merge mixed-ownership files semantically and validate them.
- Do not claim completion when the PR, permanent branch, caller, config, ruleset,
  or removal of legacy startup merging is missing.

## Determine the repository relationship

Inspect `remote.origin.url`, repository name, application layout, frontend files,
compose files, current template files, and branch model before editing.

Use this matrix:

| Target | Immediate upstream | Target branch | Sync branch | Config | Active caller |
|---|---|---|---|---|---|
| Python project | `TECHLETES/python_template@main` | repository integration branch, normally `staging` | `chore/template-sync` | `.template-sync.yml` | `.github/workflows/template-sync.yml` |
| Full-stack project | `TECHLETES/full-stack-template@main` | repository integration branch, normally `staging` | `chore/template-sync` | `.template-sync.yml` | `.github/workflows/template-sync.yml` |
| `TECHLETES/full-stack-template` | `TECHLETES/python_template@main` | `main` | `chore/python-template-sync` | `.python-template-sync.yml` | `.github/workflows/sync-python-template.yml` |
| `TECHLETES/python_template` | none | none | none | owns the defaults | owns the reusable engine |

A full-stack project must not follow `python_template` directly. If the target is
`python_template`, stop: this skill adopts downstream repositories, not the root
template into another parent.

## One-pass workflow

### 1. Preflight and audit

1. Read `AGENTS.md`, `README.md`, `pyproject.toml`, lockfiles, CI workflows,
   `.devcontainer/`, deployment files, branch model, and frontend manifests when
   present.
2. Identify the actual integration branch. Prefer the repository's established
   branch, not a guessed default.
3. Require a clean working tree. Do not stash, reset, or discard user work.
4. Record the current branch and commit.
5. Inspect existing template remotes, sync configs, caller workflows, sync
   branches, open sync PRs, and devcontainer startup scripts.
6. Detect other workflows that write back to the current PR head branch. They
   must not write to the permanent sync branch.
7. If a permanent sync branch already exists, repair it in place. Never replace
   it to simplify the task.

### 2. Load the current canonical files

Do not rely on embedded stale copies when the templates are reachable.

Configure the immediate upstream idempotently:

```bash
expected_template_url='git@github.com:TECHLETES/python_template.git' # choose from matrix
configured_template_url="$(git remote get-url template 2>/dev/null || true)"

if [ -z "$configured_template_url" ]; then
  git remote add template "$expected_template_url"
elif [ "$configured_template_url" != "$expected_template_url" ]; then
  echo "Unexpected template remote: $configured_template_url" >&2
  exit 1
fi

git remote set-url --push template DISABLED
git fetch origin --prune
git fetch template main --prune
```

Before creating files, inspect the live upstream versions:

```bash
git show template/main:.template-sync.yml
git show template/main:.github/workflows/template-sync.yml
```

Also inspect the live reusable engine from `python_template` when bootstrap
filter behavior or caller inputs must be verified.

### 3. Create or repair the permanent sync branch

For a new setup, create the permanent branch directly from the current target
branch. Do not use a temporary adoption branch.

```bash
git switch <target-branch>
git pull --ff-only origin <target-branch>
git switch -c <sync-branch>
```

If the remote sync branch already exists:

```bash
git fetch origin <sync-branch> <target-branch>
git switch <sync-branch>
git pull --ff-only origin <sync-branch>
git merge --no-edit --no-ff origin/<target-branch>
```

Stop on target-branch conflicts and resolve them normally. Do not reset the sync
branch.

### 4. Install the target-owned config and central caller

For Python and full-stack projects:

1. Start from the current upstream `.template-sync.yml`.
2. Keep `source.repository` pointed at the immediate upstream.
3. Set `target.branch` to the detected integration branch.
4. Set `target.sync_branch` to `chore/template-sync`.
5. Preserve the upstream default allowlist as the baseline. Modify it only for a
   deliberate repository-specific reason.
6. Keep `.template-sync.yml` target-owned; never include it in its own `paths`.
7. Copy the current upstream `.github/workflows/template-sync.yml` and adapt only
   relationship-specific values such as the target branch.
8. The caller must use the central engine in `python_template`, including for
   full-stack projects.

The caller must pass:

```yaml
secrets:
  app_client_id: ${{ vars.TEMPLATE_SYNC_APP_CLIENT_ID }}
  app_private_key: ${{ secrets.TEMPLATE_SYNC_APP_PRIVATE_KEY }}
```

For `full-stack-template` itself, ensure all four relationship files exist and
are correct:

```text
.github/workflows/sync-python-template.yml   # active upstream sync
.python-template-sync.yml                    # python_template -> full-stack-template
.github/workflows/template-sync.yml          # inherited downstream caller
.template-sync.yml                           # full-stack-template -> projects
```

Its active upstream values are:

```yaml
template_repository: TECHLETES/python_template
template_branch: main
target_branch: main
sync_branch: chore/python-template-sync
config_path: .python-template-sync.yml
```

Commit setup files on the permanent sync branch before the initial unrelated
history merge if Git requires a clean index.

### 5. Bootstrap the first template merge

Determine whether the current upstream commit is already an ancestor:

```bash
if git merge-base --is-ancestor template/main HEAD; then
  echo "Template ancestry already present"
else
  echo "Initial template ancestry merge required"
fi
```

For the first adoption, perform a real merge on the permanent branch:

```bash
pre_template_head="$(git rev-parse HEAD)"
git merge \
  --allow-unrelated-histories \
  --no-commit \
  --no-ff \
  template/main
```

A nonzero merge status caused by conflicts is expected. Do not abort merely
because conflicts exist.

Filter this bootstrap merge exactly like the current reusable workflow:

1. Read `paths` from the target-owned config.
2. Enumerate staged, unstaged, added, deleted, renamed, and unmerged paths.
3. For every path outside the allowlist, restore the state from
   `pre_template_head`; remove it when it did not exist there.
4. Resolve unmanaged conflicts automatically to the target state.
5. Leave only allowlisted conflicts for semantic resolution.
6. Do not implement filtering as copying files from the template. The final
   commit must remain a real two-parent merge commit.

Read the current central reusable workflow and mirror its path matching and
restore behavior for this one-time bootstrap. Do not add that implementation to
the target repository.

After resolving managed conflicts:

```bash
git add -A
git commit --allow-empty -m "chore: adopt Techletes template <template-short-sha>"
```

Verify the commit has both the previous sync-branch commit and the upstream
template commit as parents.

### 6. Merge mixed-ownership files semantically

The allowlist indicates that upstream changes must be reviewed. It does not mean
that target files must remain byte-identical.

- Application code, migrations, project data, and domain-specific docs: preserve
  the target unless the user explicitly requests migration.
- `pyproject.toml`: preserve package identity and dependencies; incorporate the
  current template tooling, Python constraints, security, testing, and quality
  settings.
- `uv.lock`: do not hand-merge. Regenerate after `pyproject.toml` is final.
- `frontend/package.json`: preserve project dependencies and scripts while
  incorporating relevant baseline updates; regenerate the project lockfile.
- Devcontainer, Docker, compose, Caddy, and workflows: preserve project-specific
  services, ports, secrets, triggers, and deployment behavior while applying
  relevant baseline improvements.
- `README.md` and `AGENTS.md`: preserve project context and add current setup and
  engineering guidance.
- `.env.template`: preserve project variables and semantics; never add real
  secrets.
- `.secret.baseline`: regenerate or audit with the configured scanner and
  investigate every new result.

Run `scripts/hooks/adopt-template.py` when present, but treat it as a helper, not
proof of correctness. Inspect its diff and correct metadata manually when
needed. Do not use the obsolete `scripts/adopt-template.py` path.

### 7. Remove legacy startup merging

Remove all template fetch, merge, stage, commit, and branch modification logic
from `post-create.sh`, `post-attach.sh`, and other startup hooks.

Devcontainer hooks may install dependencies and start services. Opening or
attaching to a devcontainer must never modify Git history or template state.

### 8. Validate the repository

Run the target repository's documented checks. At minimum for Python projects:

```bash
git diff --check
uv lock
uv sync
uv run pre-commit install --install-hooks
uv run pre-commit run --all-files
uv run pytest
```

Run documented type checks, security checks, Docker/devcontainer validation, and
frontend lint, typecheck, tests, and build where applicable. Do not suppress
failures to make the adoption appear complete. Distinguish new failures from
pre-existing failures with evidence.

Validate the sync setup:

- config source, source branch, target branch, and sync branch match the caller;
- caller uses the central reusable workflow;
- no local reusable sync engine exists;
- permanent branch contains template ancestry;
- only intended allowlisted content changed;
- no unresolved conflicts remain;
- no workflow writes generated files back to the permanent sync branch;
- legacy devcontainer merge logic is gone.

### 9. Configure and verify GitHub repository settings

Use `gh` and the GitHub API when authenticated permissions allow it. Do not leave
an automatable repository setting as a manual instruction without first trying.

Ensure a branch ruleset targets the exact permanent branch and contains only the
required protections:

- active enforcement;
- exact include `refs/heads/<sync-branch>`;
- deletion protection;
- non-fast-forward protection;
- no update restriction;
- no linear-history rule;
- no pull-request requirement on direct updates to the sync branch.

Create or update the ruleset idempotently. Do not create duplicate rulesets. A
normal merge push by the GitHub App must remain possible.

Verify or report exact blockers for:

- GitHub App `Techletes Template Sync` installed on both source and target repos;
- organization variable `TEMPLATE_SYNC_APP_CLIENT_ID` available to the target;
- organization secret `TEMPLATE_SYNC_APP_PRIVATE_KEY` available to the target;
- App permissions: Metadata read, Contents read/write, Pull requests read/write,
  and Workflows write when synchronized workflow files require it;
- `python_template` reusable-workflow access enabled for Techletes repositories.

Secret values cannot be read. Verify presence and access where the API permits;
otherwise state the exact manual check instead of claiming success.

### 10. Push and open or update the adoption PR

Push the permanent branch normally:

```bash
git push -u origin <sync-branch>
```

Open or update one PR with:

- head: the permanent sync branch;
- base: the integration branch;
- title: `chore: adopt Techletes Python template` or
  `chore: adopt Techletes full-stack template`;
- upstream repository and exact template SHA;
- allowlist summary;
- important semantic merge decisions;
- validation results and any pre-existing failures;
- repository-setting actions and remaining blockers;
- explicit instruction to **Squash and merge**;
- explicit instruction not to delete the permanent branch.

Do not open a second temporary adoption PR.

## Repair an existing partial or failed setup

When config, workflow, branch, or PR already exists:

1. Inspect before editing.
2. Preserve the permanent branch and its ancestry.
3. Replace a repository-local sync engine with the small central caller.
4. Align config and caller values exactly.
5. Merge the current target branch into the permanent branch.
6. Merge only upstream commits not already in its ancestry.
7. Update the existing PR rather than creating duplicates.
8. Revert unrelated automated writer changes with a normal commit, never reset or
   force-push.

If an early failed attempt created a branch with no useful ancestry, do not
delete it automatically. Explain the evidence and request confirmation before
any destructive cleanup.

## Later update and conflict behavior

Later updates are performed by the reusable workflow. The expected sequence is:

```text
checkout permanent sync branch
merge current target branch
merge current immediate upstream
restore non-allowlisted paths
record upstream ancestry
push permanent branch
open or update PR to target branch
```

When the workflow reports managed conflicts, resolve them on the permanent
branch, commit the real merge, push normally, and rerun the workflow. Never
reset, rebase, recreate, or force-push the branch to avoid conflicts.

## Completion evidence

Before finishing, provide:

- repository classification and immediate upstream;
- target and permanent sync branches;
- template SHA incorporated;
- config and caller paths;
- confirmation that the central reusable workflow is used;
- permanent branch ancestry evidence;
- ruleset result;
- App, variable, and secret access result or exact blocker;
- legacy startup merge removal result;
- changed-file and semantic merge summary;
- validation commands and results;
- PR URL;
- explicit remaining manual actions, especially squash merge and branch retention.

The repository is not template compliant until the permanent branch is remote,
the PR is open or updated, and every available automated setup step has been
attempted.
