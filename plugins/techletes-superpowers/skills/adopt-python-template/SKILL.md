---
name: adopt-python-template
description: Use when an active Python or Techletes full-stack repository needs to adopt or update a template baseline, including uv, devcontainers, pre-commit, secret scanning, frontend tooling, and coding-agent instructions
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

## Use Only When

- The repository is active and Python-based.
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
ask the user before merging. Use a short question such as:

> Should this adopt `python_template` (Python baseline) or
> `full-stack-template` (FastAPI/React baseline)? This determines which
> frontend, backend, devcontainer, and deployment changes it will inherit.

Do not infer the answer from a branch name or from the presence of one Python
directory. Inspect the frontend, compose/deployment files, and repository
origin first.

**REQUIRED SUB-SKILL:** Use `techletes-superpowers:verification-before-completion`
before claiming adoption is complete. Use
`techletes-superpowers:systematic-debugging` for merge, install, hook, or test
failures rather than bypassing them.

## Preflight

1. Read the target repository's `AGENTS.md`, `README.md`, `pyproject.toml`, CI
   workflows, devcontainer files, and (for full-stack targets) frontend
   manifests and compose/deployment files. Identify supported Python versions,
   package layout, test commands, deployment workflows, frontend checks, and
   secret-scan command.
2. Require a clean working tree: `git status --short` must be empty. Do not
   stash, reset, or discard the user's work.
3. Confirm whether the repository is already based on a current template
   baseline. If it is, skip first adoption entirely and use only the update
   path below to merge the latest template version into the repo.
4. Record the current branch and commit so the migration can be reviewed and
   safely abandoned without destructive Git commands.

## First Adoption

Use a dedicated branch and an idempotent remote setup. Set
`expected_template_url` from
the classification above; never copy the command below without choosing the
correct value first:

```bash
git switch -c chore/adopt-template
expected_template_url='git@github.com:TECHLETES/python_template.git'  # replace when needed
configured_template_url="$(git remote get-url template 2>/dev/null || true)"
if [ -z "$configured_template_url" ]; then
  git remote add template "$expected_template_url"
  git remote set-url --push template DISABLED
elif [ "$configured_template_url" != "$expected_template_url" ]; then
  echo "template remote points to an unexpected URL: $configured_template_url" >&2
  exit 1
fi
git fetch template
git merge template/main --allow-unrelated-histories --no-commit
```

In the snippet, keep separate variables in the real command:
`expected_template_url` is the selected upstream and `configured_template_url`
is the value read from Git. If an existing remote points elsewhere, stop and
ask whether it is intentional; never replace it silently.

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
For a full-stack target, do not import Python-template sample application code
or generic Python package directories. Keep the target's backend package,
frontend package, generated API client, and service layout.

## Conflict Ownership

| Area | Decision |
|---|---|
| Application code, migrations, domain docs | Keep target repository |
| Full-stack backend/frontend, generated client, compose, Caddy, deployment | Keep target repository; merge generic tooling around them |
| Existing dependencies and package name | Keep target repository; merge only required template tooling |
| `.devcontainer/`, pre-commit, VS Code settings, generic docs | Prefer template, then adapt project-specific paths, services, ports, and upstream URL |
| `pyproject.toml` | Merge metadata and dependencies carefully; take template tool configuration without deleting target settings |
| `uv.lock` | Never hand-merge; regenerate with `uv lock` after `pyproject.toml` is final |
| Frontend `package.json`, lockfile, build and test config | Keep target repository; preserve Bun/toolchain and service-first conventions |
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

For a full-stack target, also run the smallest documented frontend checks, for
example `bun run lint`, `bun run typecheck`, and `bun run test`; regenerate the
frontend client only when backend API changes require it. Follow the target's
`AGENTS.md` for Docker restrictions: if builds or compose startup are
prohibited, do not run them and record that limitation. Otherwise verify the
devcontainer and required services as appropriate.

If the repository has no tests, run its documented check and record that gap in
the PR. Verify that existing deployment workflows remain present and that no
real secrets entered the baseline. Commit only intended hygiene/configuration
changes, then open a separate PR for first adoption with failures and
assumptions documented.

## Later Template Updates

For an existing `template` remote, use the immediate upstream selected during
classification:

```bash
git switch -c chore/update-template
git fetch template
git merge template/main --no-commit
uv lock
uv sync
uv run pre-commit run --all-files
```

For full-stack repositories, review frontend, generated-client, compose,
deployment, and route changes separately from generic Python tooling. Do not
run the first-adoption helper during an update-only refresh.

Repeat the devcontainer and test checks. Review the diff for template drift; do
not resolve recurring conflicts by blindly taking either side.

If the repository is already adopted and only needs a template refresh, do not
run the first-adoption helper or recreate the full setup path. Limit the work to
merging the latest template changes and reconciling the resulting diff.

## Completion Evidence

The PR description must state: selected upstream and template commit merged,
metadata/package choices, files intentionally preserved, validation results,
frontend results when applicable, devcontainer result or documented reason it
was not run, secret baseline result, and any legacy gaps. Existing deployment
workflows must be visibly retained.
