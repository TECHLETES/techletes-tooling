FROM mcr.microsoft.com/devcontainers/python:1-3.12-bookworm

ARG USERNAME=vscode
ARG NODE_MAJOR=22
ARG BUN_VERSION=1.4.2
ARG CODEX_VERSION=0.154.0

LABEL org.opencontainers.image.source="https://github.com/TECHLETES/techletes-tooling" \
      org.opencontainers.image.description="Shared Techletes development container"

USER root

# PostgreSQL's Bookworm repository provides a client matching the PostgreSQL 18
# service version used by the Techletes full-stack template.
RUN install -d -m 0755 /usr/share/postgresql-common/pgdg \
    && curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc \
      | gpg --dearmor -o /usr/share/postgresql-common/pgdg/apt.postgresql.org.gpg \
    && echo "deb [signed-by=/usr/share/postgresql-common/pgdg/apt.postgresql.org.gpg] https://apt.postgresql.org/pub/repos/apt bookworm-pgdg main" \
      > /etc/apt/sources.list.d/pgdg.list

RUN rm -f /etc/apt/sources.list.d/yarn.list \
    && apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
      apt-transport-https \
      bubblewrap \
      build-essential \
      ca-certificates \
      curl \
      direnv \
      gnupg \
      iproute2 \
      jq \
      libmariadb-dev \
      libpq-dev \
      lsof \
      mariadb-client \
      netcat-openbsd \
      odbc-mariadb \
      openssh-client \
      postgresql-client-18 \
      procps \
      redis-tools \
      ripgrep \
      socat \
      unixodbc \
      unixodbc-dev \
      unzip \
    && rm -rf /var/lib/apt/lists/*

# Install the 1Password CLI from its official apt repository. The resulting
# package version is frozen by the immutable published image release.
RUN curl -fsSL https://downloads.1password.com/linux/keys/1password.asc \
      | gpg --dearmor -o /usr/share/keyrings/1password-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/1password-archive-keyring.gpg] https://downloads.1password.com/linux/debian/$(dpkg --print-architecture) stable main" \
      > /etc/apt/sources.list.d/1password.list \
    && apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends 1password-cli \
    && rm -rf /var/lib/apt/lists/*

# Node is needed by the frontend toolchain and Codex CLI. Bun and Codex are
# explicitly versioned so rebuilding a release cannot silently upgrade them.
RUN curl -fsSL "https://deb.nodesource.com/setup_${NODE_MAJOR}.x" | bash - \
    && apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends nodejs \
    && npm install --global "bun@${BUN_VERSION}" "@openai/codex@${CODEX_VERSION}" \
    && node --version \
    && bun --version \
    && codex --version \
    && npm cache clean --force \
    && rm -rf /var/lib/apt/lists/*

# uv comes from its versioned official image rather than a mutable install
# script. This COPY is multi-architecture when the parent build is multi-arch.
COPY --from=ghcr.io/astral-sh/uv:0.12.13 /uv /uvx /usr/local/bin/

COPY scripts/techletes-dev /usr/local/bin/techletes-dev
COPY scripts/verify-image.sh /usr/local/share/techletes/verify-image.sh

RUN chmod 0755 /usr/local/bin/techletes-dev /usr/local/share/techletes/verify-image.sh \
    && mkdir -p \
      /home/${USERNAME}/.cache/uv \
      /home/${USERNAME}/.cache/pre-commit \
      /home/${USERNAME}/.cache/bun \
    && chown -R ${USERNAME}:${USERNAME} /home/${USERNAME}/.cache

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TZ=Europe/Amsterdam

USER ${USERNAME}
