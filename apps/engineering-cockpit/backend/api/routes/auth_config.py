"""Consolidated authentication configuration endpoint."""

from fastapi import APIRouter
from pydantic import BaseModel

from backend.core.auth.entra import EntraAuthClient
from backend.core.config import settings

router = APIRouter(prefix="/auth", tags=["auth-config"])


class EntraProviderConfig(BaseModel):
    """Microsoft Entra configuration."""

    enabled: bool
    client_id: str | None = None
    tenant_id: str | None = None
    authority: str | None = None


class GoogleProviderConfig(BaseModel):
    """Google OAuth configuration."""

    enabled: bool
    client_id: str | None = None


class GitHubProviderConfig(BaseModel):
    """GitHub OAuth configuration."""

    enabled: bool
    client_id: str | None = None


class AppConfigData(BaseModel):
    """Application-wide configuration."""

    signup_enabled: bool


class ConsolidatedAuthConfig(BaseModel):
    """Consolidated authentication and app configuration for all auth providers."""

    entra: EntraProviderConfig
    google: GoogleProviderConfig
    github: GitHubProviderConfig
    app: AppConfigData


@router.get("/config", response_model=ConsolidatedAuthConfig)
def get_consolidated_auth_config() -> ConsolidatedAuthConfig:
    """
    Get consolidated authentication configuration for all providers.

    This single endpoint returns configuration for Entra, Google, GitHub,
    and general app settings, reducing the number of API calls needed
    on the login screen from 5 to 1.

    Returns:
        ConsolidatedAuthConfig with all provider configs and app settings
    """
    authority = None
    if settings.azure_enabled:
        authority = EntraAuthClient().get_authority()

    return ConsolidatedAuthConfig(
        entra=EntraProviderConfig(
            enabled=settings.azure_enabled,
            client_id=settings.AZURE_CLIENT_ID if settings.azure_enabled else None,
            tenant_id=settings.AZURE_TENANT_ID if settings.azure_enabled else None,
            authority=authority,
        ),
        google=GoogleProviderConfig(
            enabled=settings.google_enabled,
            client_id=settings.GOOGLE_CLIENT_ID if settings.google_enabled else None,
        ),
        github=GitHubProviderConfig(
            enabled=settings.github_enabled,
            client_id=settings.GITHUB_CLIENT_ID if settings.github_enabled else None,
        ),
        app=AppConfigData(signup_enabled=settings.SIGNUP_ENABLED),
    )
