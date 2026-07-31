"""Backend application entrypoint and FastAPI app setup."""

import logging
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.routing import APIRoute
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware

from backend.api.main import api_router
from backend.cockpit.runtime_instance import (
    RuntimeInstanceAlreadyRunning,
    RuntimeInstanceLock,
)
from backend.core.config import settings

logger = logging.getLogger(__name__)


def _default_lock_path() -> Path:
    """Return a per-user runtime path for the process ownership lock."""
    runtime_dir = os.environ.get("XDG_RUNTIME_DIR")
    if runtime_dir:
        return Path(runtime_dir) / "techletes-engineering-cockpit.lock"
    return (
        Path.home()
        / ".cache"
        / "techletes-engineering-cockpit"
        / "instance.lock"
    )


def custom_generate_unique_id(route: APIRoute) -> str:
    """Generate consistent route IDs for OpenAPI documentation."""
    return f"{route.tags[0]}-{route.name}"


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown events."""
    configured_lock_path = os.environ.get("COCKPIT_INSTANCE_LOCK_PATH")
    lock_path = (
        Path(configured_lock_path)
        if configured_lock_path
        else _default_lock_path()
    )
    try:
        instance_lock = RuntimeInstanceLock.acquire(lock_path)
    except RuntimeInstanceAlreadyRunning as exc:
        logger.error("%s", exc)
        raise
    logger.info("""
╔══════════════════════════════════════════════════════════════════════════════════════╗
║                                      Powered by                                      ║
║                                                                                      ║
║   ████████╗███████╗ ██████╗██╗  ██╗██╗     ███████╗████████╗███████╗███████╗         ║
║   ╚══██╔══╝██╔════╝██╔════╝██║  ██║██║     ██╔════╝╚══██╔══╝██╔════╝██╔════╝         ║
║      ██║   █████╗  ██║     ███████║██║     █████╗     ██║   █████╗  ███████╗         ║
║      ██║   ██╔══╝  ██║     ██╔══██║██║     ██╔══╝     ██║   ██╔══╝  ╚════██║  ██╗    ║
║      ██║   ███████╗╚██████╗██║  ██║███████╗███████╗   ██║   ███████╗███████║   ╚██╗  ║
║      ╚═╝   ╚══════╝ ╚═════╝╚═╝  ╚═╝╚══════╝╚══════╝   ╚═╝   ╚══════╝╚══════╝  ██╔╝   ║
║                                                                                      ║
╚══════════════════════════════════════════════════════════════════════════════════════╝
    """)
    try:
        yield
    finally:
        instance_lock.release()


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
    lifespan=lifespan,
)

# Set all CORS enabled origins
if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)

# Mount static files for the frontend (SPA)
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="frontend")
