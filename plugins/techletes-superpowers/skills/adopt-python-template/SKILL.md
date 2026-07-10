---
name: adopt-python-template
description: Use when an active Python repository needs to adopt or update the Techletes Python template baseline, including uv, devcontainers, pre-commit, secret scanning, VS Code settings, and coding-agent instructions
---

# Adopt the Techletes Python Template

Bring an active Python repository onto the Techletes Python template without
rewriting its application. The template owns generic developer tooling; the
target repository owns its product code, dependencies, deployment behavior,
package identity, and domain documentation.

## Use Only When

- The repository is active and Python-based.
- No explicit client or product requirement mandates another baseline.
- A separate migration PR is acceptable for first adoption.

Stop and report instead of merging for archived repositories, temporary scripts,
non-Python repositories, or unclear ownership of production configuration.

**REQUIRED SUB-SKILL:** Use `techletes-superpowers:verification-before-completion`
before claiming adoption is complete. Use
`techletes-superpowers:systematic-debugging` for merge, install, hook, or test
failures rather than bypassing them.

## Preflight

1. Read the target repository's `AGENTS.md`, `README.md`, `pyproject.toml`, CI
   workflows, and devcontainer files. Identify supported Python versions,
   package layout, test command, deployment workflows, and secret-scan command.
2. Require a clean working tree: `git status --short` must be empty. Do not
   stash, reset, or discard the user's work.
3. Confirm the repository is not already based on a current template baseline.
   If it is, use the update path below instead of a first-adoption merge.
4. Record the current branch and commit so the migration can be reviewed and
   safely abandoned without destructive Git commands.

## First Adoption

Use a dedicated branch and an idempotent remote setup:

```bash
git switch -c chore/adopt-python-template
template_url="$(git remote get-url template 2>/dev/null || true)"
if [ -z "$template_url" ]; then
  git remote add template git@github.com:TECHLETES/python_template.git
elif [ "$template_url" != "git@github.com:TECHLETES/python_template.git" ]; then
  echo "template remote points to an unexpected URL: $template_url" >&2
  exit 1
fi
git fetch template
git merge template/main --allow-unrelated-histories --no-commit
```

Do not commit until conflicts are resolved and the merged tree has been
inspected. If the remote exists with a different URL, stop and ask whether it
is the intended template; never replace it silently.

Run the template's existing adoption helper after the merge. Prefer discovered
project metadata; pass explicit values when inference would be wrong:

```bash
uv run python scripts/adopt-template.py \
  --name my-repository \
  --package my_package \
  --description "Short project description."
```

Do not invent a second migration script or manually copy template files.

## Conflict Ownership

| Area | Decision |
|---|---|
| Application code, migrations, domain docs | Keep target repository |
| Existing dependencies and package name | Keep target repository; merge only required template tooling |
| `.devcontainer/`, pre-commit, VS Code settings, generic docs | Prefer template, then adapt project-specific paths |
| `pyproject.toml` | Merge metadata and dependencies carefully; take template tool configuration without deleting target settings |
| `uv.lock` | Never hand-merge; regenerate with `uv lock` after `pyproject.toml` is final |
| Deployment and release workflows | Preserve; add compatible quality jobs without removing triggers, secrets, or release steps |
| `.envrc`, `.env.template`, client config | Preserve variables and semantics; add only documented generic entries |
| `README.md`, `AGENTS.md` | Preserve project context and add the new setup/quality workflow |
| `.secret.baseline` | Re-scan using the repository's configured tool; investigate every new finding, never suppress secrets blindly |

When a conflict cannot be classified from the repository, stop before choosing
the template version. A successful merge is not evidence that the result is
safe.

## Finish and Verify

After resolving conflicts and applying metadata:

```bash
git diff --check
uv lock
uv sync
uv run pre-commit install --install-hooks
uv run pre-commit run --all-files
uv run pytest
```

If the repository has no tests, run its documented check and record that gap in
the PR. Rebuild or reopen the repository in the devcontainer and verify that
the container builds and `uv sync` succeeds inside it. Verify that existing
deployment workflows remain present and that no real secrets entered the
baseline. Commit only the intended hygiene/configuration changes, then open a
separate PR for first adoption with failures and assumptions documented.

## Later Template Updates

For an existing `template` remote:

```bash
git switch -c chore/update-python-template
git fetch template
git merge template/main --no-commit
uv run python scripts/adopt-template.py
uv lock
uv sync
uv run pre-commit run --all-files
```

Repeat the devcontainer and test checks. Review the diff for template drift; do
not resolve recurring conflicts by blindly taking either side.

## Completion Evidence

The PR description must state: template commit merged, metadata/package choices,
files intentionally preserved, validation results, devcontainer result, secret
baseline result, and any documented legacy gaps. Existing deployment workflows
must be visibly retained.
