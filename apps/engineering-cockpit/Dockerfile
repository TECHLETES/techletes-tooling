# Stage 1: Build frontend with Bun
FROM oven/bun:1 AS frontend-builder

WORKDIR /app

COPY frontend/package.json frontend/bun.lock /app/frontend/

WORKDIR /app/frontend

# Use BuildKit cache mount for bun dependencies
# Ref: https://docs.docker.com/build/cache/
RUN --mount=type=cache,target=/root/.bun \
    bun install

COPY ./frontend /app/frontend

ARG COMMIT_SHA=local
ENV VITE_APP_BUILD_ID=$COMMIT_SHA

RUN bun run build


# Stage 2: Build and run backend with frontend static files
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1

# Install curl for healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Install uv
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#installing-uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Compile bytecode
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#compiling-bytecode
ENV UV_COMPILE_BYTECODE=1

# uv Cache
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#caching
ENV UV_LINK_MODE=copy

WORKDIR /app/

# Place executables in the environment at the front of the path
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#using-the-environment
ENV PATH="/app/.venv/bin:$PATH"

# Add /app to PYTHONPATH so backend package imports work from scripts
ENV PYTHONPATH="/app"

# Install backend dependencies (without the project itself for layer caching)
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#intermediate-layers
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-dev --no-install-workspace

COPY ./backend /app/backend

COPY ./pyproject.toml /app/

# Sync the project (install the backend package itself)
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#intermediate-layers
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-dev

# Copy built frontend to backend static directory
COPY --from=frontend-builder /app/frontend/dist /app/backend/static

# Copy entrypoint script in-place so its repo-root detection still resolves to /app
RUN chmod +x /app/backend/scripts/entrypoint.sh

WORKDIR /app/backend/

ENTRYPOINT ["/app/backend/scripts/entrypoint.sh"]
