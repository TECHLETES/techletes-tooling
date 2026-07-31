"""Shared backend constants."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class RoleConstants:
    """Canonical application role names."""

    VIEWER: str = "viewer"
    USER: str = "user"
    ADMIN: str = "admin"
    SUPER_ADMIN: str = "super_admin"


@dataclass(frozen=True)
class EntraConstants:
    """Microsoft Entra and Microsoft Graph constants."""

    DEFAULT_TENANT: str = "organizations"
    GRAPH_API_BASE_URL: str = "https://graph.microsoft.com/v1.0"
    APP_ROLE_MEMBER_TYPE_USER: str = "User"
    APP_ROLE_ID_NAMESPACE: str = "techletes/entra/app-roles"


@dataclass(frozen=True)
class Constants:
    """Root constants namespace."""

    roles: RoleConstants = field(default_factory=RoleConstants)
    entra: EntraConstants = field(default_factory=EntraConstants)


constants = Constants()
