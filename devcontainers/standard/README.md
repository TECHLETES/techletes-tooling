# Techletes Standard Devcontainer

This component owns the shared Techletes developer environment published to GitHub Container Registry as:

```text
ghcr.io/techletes/devcontainer
```

The image is intended to replace duplicated `.devcontainer/Dockerfile` files across Techletes repositories. Application repositories keep their own project dependencies, Compose services, ports, environment bootstrap, lifecycle scripts, and credentials.

## Baseline

The initial image deliberately follows the existing Techletes Python/full-stack devcontainers instead of combining the migration with a platform upgrade:

- Python 3.12 on Debian Bookworm
- uv 0.12.13
- Node.js 22
- Bun 1.4.2
- Codex CLI 0.154.0
- Azure CLI 2.90.0 with Bicep
- Docker CLI/Compose through Docker-outside-of-Docker
- Git and GitHub CLI
- 1Password CLI
- PostgreSQL 18 client and libpq development files
- MariaDB client and Connector/C development files
- unixODBC plus the MariaDB ODBC driver
- Redis CLI
- common diagnostics such as `jq`, `ripgrep`, `lsof`, `iproute2`, `netcat`, `socat`, `procps`, and SSH client tooling

The image also embeds the shared Techletes full-stack Dev Container metadata: the `vscode` remote user, Amsterdam timezone, uv/pre-commit environment defaults, reusable cache volumes, and the editor extensions/settings used by the current full-stack repositories.

### Shared VS Code baseline

The shared image intentionally carries the full common Techletes editor baseline rather than only Python tooling. It includes:

- Python, Pylance, mypy, Ruff, Black, debugpy, and Jupyter
- both Docker editor integrations currently used by Techletes repositories
- GitHub Actions and GitHub Pull Requests
- OpenAI ChatGPT/Codex integration
- TOML, YAML, and shell tooling
- Biome and ESLint
- Tailwind CSS and Playwright
- SQLTools with MySQL/MariaDB, PostgreSQL, and SQLite drivers
- Microsoft PostgreSQL tooling
- Office/document viewing
- Caddyfile support

JavaScript, JSX, TypeScript, and TSX use the same Biome-on-save defaults as the current Techletes full-stack template, with `biome.requireConfiguration` enabled so repositories are expected to opt in through their committed Biome configuration. Python keeps Black as formatter and Ruff for fixes/import organization.

Consuming repositories can still add extensions and override settings locally. The goal is that a normal Techletes full-stack repository does not need to repeat the standard extension list.

## Boundaries

The image intentionally does **not** contain:

- application Python packages or `.venv`
- frontend `node_modules`
- project-specific browser binaries/model weights
- databases or other application services
- project-specific environment values
- GitHub, Azure, SSH, Codex, or 1Password credentials
- project-specific ports or lifecycle commands

Credentials must remain explicit at repository/user level. Do not add credential mounts such as `~/.ssh`, `~/.config/gh`, `~/.azure`, or `~/.codex` to the shared image metadata.

## Consuming the image

### Single-container repository

After the first stable image release, a small repository configuration can look like:

```json
{
  "name": "My Techletes project",
  "image": "ghcr.io/techletes/devcontainer:1.0.0",
  "postCreateCommand": "bash .devcontainer/post-create.sh",
  "waitFor": "postCreateCommand"
}
```

Use an exact release rather than `edge` for normal development. For maximum reproducibility, append the published digest after the first pull:

```text
ghcr.io/techletes/devcontainer:1.0.0@sha256:<digest>
```

### Compose-based repository

Replace the duplicated app image build in `.devcontainer/docker-compose.yml`:

```yaml
services:
  app:
    image: ghcr.io/techletes/devcontainer:1.0.0
    volumes:
      - ..:/workspaces/app:cached
```

The repository's `devcontainer.json` should retain its orchestration details:

```json
{
  "name": "My Techletes application",
  "dockerComposeFile": ["docker-compose.yml"],
  "service": "app",
  "workspaceFolder": "/workspaces/app",
  "overrideCommand": true,
  "shutdownAction": "stopCompose",
  "runServices": ["db", "redis"],
  "initializeCommand": "bash ${localWorkspaceFolder}/.devcontainer/initialize.sh",
  "postCreateCommand": "bash .devcontainer/post-create.sh",
  "waitFor": "postCreateCommand"
}
```

Repository configuration is merged with the metadata embedded in the prebuilt image. Extensions are additive and repository settings can override shared settings. Do not depend on an empty array to remove inherited mounts/features/lifecycle behavior; keep shared image metadata limited to behavior that is safe everywhere.

## Project-specific extensions

The shared image already includes the normal Python and full-stack editor stack. Repositories should add only genuine exceptions, for example a framework-specific extension, a nonstandard language toolchain, or a project-specific database/client integration not already covered by the shared baseline.

If a repository intentionally uses a different JavaScript formatter/linter strategy, it should override the relevant language settings locally rather than remove the shared extensions. Extensions are cheap to inherit; conflicting editor behavior should be resolved explicitly in repository settings.

## Project bootstrap

Project dependencies remain locked by each project. A typical `post-create.sh` should do roughly:

```bash
#!/usr/bin/env bash
set -euo pipefail

uv sync --locked
bun --cwd frontend install --frozen-lockfile
uv run pre-commit install --install-hooks
techletes-dev git-setup
```

Do not update globally installed tooling from a lifecycle hook. In particular, do not run `npm install -g @openai/codex@latest` or execute a mutable remote setup script automatically on attach. Shared tools are upgraded by releasing a new image.

The helper command provides:

```bash
techletes-dev doctor
techletes-dev versions
techletes-dev git-setup
```

## Authentication

The image includes the CLIs but no authentication state.

Repositories that need host GitHub/Codex configuration can add explicit mounts such as:

```json
{
  "mounts": [
    "source=${localEnv:HOME}/.gitconfig,target=/tmp/host-gitconfig,type=bind,consistency=cached",
    "source=${localEnv:HOME}/.codex,target=/home/vscode/.codex,type=bind,consistency=cached",
    "source=${localEnv:HOME}/.config/gh,target=/home/vscode/.config/gh,type=bind,consistency=cached"
  ]
}
```

Only add SSH access to repositories that actually need it; prefer agent forwarding to mounting private-key directories where practical.

Azure CLI is part of every shared image because Techletes projects use Azure-backed operational/backup workflows, but Azure login/subscription/storage configuration is deliberately not embedded.

## Versioning

Image releases use tags prefixed with `devcontainer-v` in this repository:

```text
devcontainer-v1.0.0
```

A release publishes:

```text
ghcr.io/techletes/devcontainer:1.0.0
ghcr.io/techletes/devcontainer:1.0
ghcr.io/techletes/devcontainer:1
```

The exact semantic version is immutable by policy. Major/minor aliases are convenience pointers. `edge` is rebuilt from `main` and is only for validation/early adoption.

Breaking changes to language/runtime majors, removal of a shared tool, or incompatible metadata behavior require a major version bump. Normal tool upgrades use minor releases; fixes use patch releases.

## CI and release

Pull requests changing the shared image run `.github/workflows/devcontainer-check.yml`. It builds through Dev Container CLI 0.89.0 so Features are actually preinstalled and their metadata is embedded in the resulting image. CI then verifies the expected toolchain and `devcontainer.metadata` label, including representative full-stack extensions.

`.github/workflows/devcontainer-release.yml` validates first and publishes multi-platform `linux/amd64` + `linux/arm64` images. Pushes to `main` publish `edge`; a `devcontainer-vX.Y.Z` tag publishes stable semantic tags. Stable tags refuse to overwrite an existing exact version.

The first GHCR package publication may require a one-time package visibility decision in GitHub. Make the package public if anonymous pulls are required. If the package remains private, developers must authenticate Docker to GHCR before VS Code can pull the devcontainer image.

## Updating tool versions

1. Change the pinned versions in `Dockerfile` and/or `.devcontainer/devcontainer.json`.
2. Update `CHANGELOG.md`.
3. Let the PR image checks pass.
4. Merge to `main` and validate the automatically published `edge` image.
5. Create a `devcontainer-vX.Y.Z` tag from the tested `main` commit.
6. Migrate repositories with normal PRs; use exact versions and optionally a digest.

Do not modify an existing exact semantic tag.
