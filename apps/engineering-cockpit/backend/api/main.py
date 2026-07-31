"""API router registration for all backend routes."""

from fastapi import APIRouter

from backend.api.routes import (
    admin,
    auth_config,
    auth_entra,
    auth_github,
    auth_google,
    files,
    items,
    login,
    notifications,
    private,
    rbac,
    tasks,
    users,
    utils,
)
from backend.core.config import settings

api_router = APIRouter()
api_router.include_router(auth_config.router)
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(utils.router)
api_router.include_router(items.router)
api_router.include_router(rbac.router)
api_router.include_router(auth_entra.router)
api_router.include_router(auth_entra.tenant_router)
api_router.include_router(auth_google.router)
api_router.include_router(auth_github.router)
api_router.include_router(notifications.router)
api_router.include_router(files.router)
api_router.include_router(tasks.router)
api_router.include_router(admin.router)


if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)
