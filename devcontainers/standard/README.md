# Techletes Standard Devcontainer

This component owns the shared Techletes developer environment published to GitHub Container Registry as:

```text
ghcr.io/techletes/devcontainer
```

The image is intended to replace duplicated devcontainer tooling across Techletes repositories. Application repositories keep their own Compose services, ports, credentials, and genuine project-specific lifecycle behavior.

## Baseline

The shared image currently provides:

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

It also embeds the common Techletes VS Code/devcontainer metadata and editor baseline.

## Shared lifecycle commands

Common lifecycle behavior is implemented by `techletes-dev` inside the image. Repositories should call these commands directly instead of copying shell scripts.

### Python projects

```json
{
  "postCreateCommand": "techletes-dev post-create python",
  "postAttachCommand": "techletes-dev post-attach"
}
```

The Python profile:

- runs `uv sync --locked`
- installs/refreshes `graphifyy` as a uv tool
- installs repository pre-commit hooks when inside a Git worktree
- checks notebook/ipykernel availability
- reports 1Password CLI availability
- applies the shared Git setup
- prints the WSL filesystem recommendation

### Full-stack projects

```json
{
  "postCreateCommand": "techletes-dev post-create full-stack",
  "postAttachCommand": "techletes-dev post-attach"
}
```

The full-stack profile performs the Python profile behavior plus:

- creates `/app/uploads`
- requires a `frontend/` directory
- runs `bun install --frozen-lockfile` in `frontend/`

### Attach behavior

`techletes-dev post-attach` skips CI and refreshes the Techletes Codex plugin through `setup.techletes.ai`. Failure is reported but does not block attaching to the container. Codex CLI itself remains image-managed and is not self-updated on attach.

These lifecycle commands are deliberately **not** embedded as `postCreateCommand` or `postAttachCommand` in image metadata. Dev Container lifecycle commands are additive when inherited, so keeping the invocation repo-side makes ordering explicit and lets specialized repositories replace or wrap the standard profile without accidentally running both implementations.

Repositories with genuinely different bootstrap needs may keep a local script and call shared helpers from it, for example:

```bash
techletes-dev post-create python
# project-specific setup here
```

## Shared VS Code baseline

The shared image carries the common Techletes editor stack, including Python/Pylance/mypy/Ruff/Black/debugpy/Jupyter, Docker tooling, GitHub integrations, ChatGPT/Codex integration, TOML/YAML/shell tooling, Biome/ESLint, Tailwind, Playwright, SQLTools/database drivers, PostgreSQL tooling, Office viewing, and Caddyfile support.

JavaScript, JSX, TypeScript, and TSX use the standard Biome-on-save defaults with `biome.requireConfiguration` enabled. Python uses Black for formatting and Ruff for fixes/import organization.

## Boundaries

The image intentionally does **not** contain application Python packages, `.venv`, frontend `node_modules`, project databases/services, project-specific environment values, or credentials. GitHub, Azure, SSH, Codex, and 1Password authentication remain explicit at repository/user level.

Do not add credential mounts such as `~/.ssh`, `~/.config/gh`, `~/.azure`, or `~/.codex` to the shared image metadata.

## Consuming the image

A single-container project can reference the image directly. A Compose-based project should reference the image from its app service and retain its own database/Redis/etc. services.

Repositories may follow `latest` or pin an immutable/exact build according to their rollout policy. Repository configuration is merged with metadata embedded in the prebuilt image; extensions are additive and repository settings can override shared settings.

## Helper commands

```bash
techletes-dev doctor
techletes-dev versions
techletes-dev git-setup
techletes-dev post-create python
techletes-dev post-create full-stack
techletes-dev post-attach
```

## Authentication

The image includes CLIs but no authentication state. Repositories that need host GitHub/Codex configuration can mount host configuration explicitly. Prefer SSH agent forwarding over mounting private-key directories where practical.

Azure CLI is part of every shared image because Techletes projects use Azure-backed operational/backup workflows, but Azure login/subscription/storage configuration is not embedded.

## Versioning and release

Validated shared-image changes merged to `main` publish `edge` and `latest`. Stable `devcontainer-vX.Y.Z` tags publish exact semantic versions plus major/minor aliases. Exact stable tags are immutable.

Pull requests changing the shared image run `.github/workflows/devcontainer-check.yml`. The release workflow validates and publishes multi-platform `linux/amd64` + `linux/arm64` images.

When changing shared lifecycle behavior, merge and publish the shared image first, then update consuming repositories to an image build that contains the new `techletes-dev` commands.
