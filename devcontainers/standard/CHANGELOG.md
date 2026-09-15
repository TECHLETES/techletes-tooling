# Shared Devcontainer Changelog

## 1.0.0 - planned

Initial shared Techletes development image.

- Python 3.12 on Debian Bookworm.
- uv 0.12.13.
- Node.js 22.
- Bun 1.4.2.
- Codex CLI 0.154.0.
- Azure CLI 2.90.0 with Bicep.
- Docker-outside-of-Docker support.
- Git and GitHub CLI.
- 1Password CLI.
- PostgreSQL 18 client and development libraries.
- MariaDB client, Connector/C development libraries, unixODBC, and MariaDB ODBC driver.
- Redis client and common shell/network diagnostics.
- Shared Dev Container metadata for the `vscode` user, cache volumes, Python/editor defaults, and the Techletes full-stack VS Code baseline.
- Full-stack editor baseline includes Jupyter, Biome, ESLint, Tailwind CSS, Playwright, SQLTools with MySQL/PostgreSQL/SQLite drivers, Microsoft PostgreSQL tooling, Office viewing, Caddyfile support, Docker tooling, GitHub tooling, and Codex/ChatGPT.
- Persistent shared caches for uv, pre-commit, and Bun.
- Build layers isolate independently versioned tools, with Codex installed late so Codex-only updates can reuse the expensive shared layers.
- GitHub Actions persists a BuildKit `mode=max` cache across devcontainer checks and between release validation/publish jobs.
- Successful publishes trigger GHCR retention cleanup that keeps the three newest top-level devcontainer images while preserving required multi-architecture child manifests.
