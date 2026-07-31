"""Microsoft Entra authentication and tenant management endpoints."""

import logging
from datetime import timedelta
from typing import Any

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel
from sqlmodel import Session, func, select

from backend.api.deps import CurrentUser, SessionDep
from backend.core.auth import security
from backend.core.auth.entra import EntraAuthClient
from backend.core.config import settings
from backend.core.constants import constants
from backend.crud_rbac import assign_role_to_user, remove_role_from_user
from backend.models import (
    Message,
    MicrosoftTenant,
    MicrosoftTenantCreate,
    MicrosoftTenantPublic,
    MicrosoftTenantsPublic,
    MicrosoftTenantUpdate,
    Role,
    Token,
    User,
    UserRole,
    UserTenantRole,
)

router = APIRouter(prefix="/auth/entra", tags=["auth-entra"])
logger = logging.getLogger(__name__)


def _normalize_entra_role_name(role_name: str) -> str:
    """Map configured Entra superuser/admin roles to the local super_admin role."""
    if (
        role_name.casefold() == settings.AZURE_SUPERUSER_ROLE.casefold()
        or role_name.casefold() == constants.roles.SUPER_ADMIN.casefold()
        or role_name.casefold() == constants.roles.ADMIN.casefold()
    ):
        return constants.roles.SUPER_ADMIN
    return role_name


def _sync_azure_roles_to_app_roles(
    session: Session,
    user: User,
    azure_roles: list[str],
) -> None:
    """
    Sync Azure role strings to app-level Role assignments in UserRole table.

    For each Azure role name, find the matching app Role (case-insensitive)
    and assign it to the user. If a role doesn't exist, create it automatically.
    Remove any existing role assignments that are not in the current Azure roles list.
    """
    from backend.crud_rbac import create_role

    # Map Azure role names to app Role IDs (case-insensitive lookup).
    # Roles must use underscore format (e.g., "super_admin", "admin", "viewer").
    app_role_ids_to_assign = set()
    for azure_role_name in azure_roles:
        normalized_role_name = _normalize_entra_role_name(azure_role_name)
        # Try exact match first (case-insensitive)
        db_role = session.exec(
            select(Role).where(
                func.lower(Role.name) == func.lower(normalized_role_name)
            )
        ).first()

        if not db_role:
            # Auto-create role if it doesn't exist (for custom/non-system roles)
            from backend.models import RoleCreate

            db_role = create_role(
                session=session,
                role_in=RoleCreate(
                    name=normalized_role_name,
                    description=f"Role synced from Microsoft Entra: {normalized_role_name}",
                    permission_ids=[],
                ),
                is_system=False,
            )

        if db_role:
            app_role_ids_to_assign.add(db_role.id)

    # Get current role assignments for this user
    current_user_roles = session.exec(
        select(UserRole).where(UserRole.user_id == user.id)
    ).all()
    current_role_ids = {ur.role_id for ur in current_user_roles}

    # Remove roles that are no longer in Azure roles
    for role_id in current_role_ids - app_role_ids_to_assign:
        remove_role_from_user(session=session, user_id=user.id, role_id=role_id)

    # Add new roles from Azure
    for role_id in app_role_ids_to_assign - current_role_ids:
        assign_role_to_user(session=session, user_id=user.id, role_id=role_id)


class EntraLoginRequest(BaseModel):
    """Request body for Microsoft Entra login."""

    id_token: str


class EntraLoginUrlResponse(BaseModel):
    """Response schema containing the Entra login URL."""

    login_url: str


@router.post("/login", response_model=Token)
def entra_login(
    request: EntraLoginRequest,
    response: Response,
    session: SessionDep,
) -> Any:
    """
    Authenticate via Microsoft Entra.

    Accepts a Microsoft Entra ID token, verifies it for this application,
    and returns an application JWT.
    """
    if not settings.azure_enabled:
        raise HTTPException(
            status_code=400, detail="Microsoft Entra authentication is not configured"
        )

    entra_client = EntraAuthClient()

    try:
        verified_claims = entra_client.verify_id_token(request.id_token)
    except Exception as err:
        logger.exception("Microsoft Entra login failed during ID token verification")
        detail = "Failed to validate Microsoft ID token"
        if settings.ENVIRONMENT == "local":
            detail = f"{detail}: {err}"
        raise HTTPException(status_code=400, detail=detail) from err

    email: str | None = (
        verified_claims.get("preferred_username")
        or verified_claims.get("email")
        or verified_claims.get("upn")
    )
    if not email:
        logger.error(
            "Microsoft Entra token missing email-related claims: %s",
            sorted(verified_claims.keys()),
        )
        raise HTTPException(
            status_code=400, detail="Could not retrieve email from Microsoft account"
        )

    azure_user_id: str = verified_claims.get("oid") or verified_claims.get("sub", "")
    if not azure_user_id:
        logger.error(
            "Microsoft Entra token missing user identifier claims: %s",
            sorted(verified_claims.keys()),
        )
        raise HTTPException(
            status_code=400, detail="Could not retrieve user ID from Microsoft token"
        )
    azure_tenant_id: str | None = verified_claims.get("tid")
    user_roles = [
        role
        for role in verified_claims.get("roles", [])
        if isinstance(role, str) and role.strip()
    ]

    # Find or create user
    db_user = session.exec(select(User).where(User.email == email)).first()

    # Check if user has superuser role (must use underscore format: "super_admin")
    is_admin = any(
        role.casefold() == settings.AZURE_SUPERUSER_ROLE.casefold()
        or role.casefold() == constants.roles.SUPER_ADMIN.casefold()
        for role in user_roles
    )

    if not db_user:
        db_user = User(
            email=email,
            full_name=verified_claims.get("name"),
            azure_user_id=azure_user_id,
            azure_tenant_id=azure_tenant_id,
            azure_roles=user_roles,
            is_active=True,
            is_superuser=is_admin,
        )
        session.add(db_user)
    else:
        # Sync user info from Microsoft on each login
        db_user.full_name = verified_claims.get("name") or db_user.full_name
        db_user.azure_user_id = azure_user_id
        db_user.azure_tenant_id = azure_tenant_id
        db_user.azure_roles = user_roles
        db_user.is_superuser = is_admin
        session.add(db_user)

    session.commit()
    session.refresh(db_user)

    # Sync Azure roles to app-level roles (UserRole table)
    _sync_azure_roles_to_app_roles(session, db_user, user_roles)

    # Sync tenant roles
    if azure_tenant_id:
        ms_tenant = session.exec(
            select(MicrosoftTenant).where(
                MicrosoftTenant.tenant_id == azure_tenant_id,
            )
        ).first()
        if ms_tenant:
            tenant_role = session.exec(
                select(UserTenantRole).where(
                    UserTenantRole.user_id == db_user.id,
                    UserTenantRole.tenant_id == ms_tenant.id,
                )
            ).first()
            if tenant_role:
                tenant_role.roles = user_roles
                session.add(tenant_role)
            else:
                tenant_role = UserTenantRole(
                    user_id=db_user.id,
                    tenant_id=ms_tenant.id,
                    roles=user_roles,
                )
                session.add(tenant_role)
            session.commit()

    if not db_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        db_user.id, expires_delta=access_token_expires
    )
    security.set_auth_cookies(response, access_token)
    return Token(access_token=access_token)


@router.get("/login-url", response_model=EntraLoginUrlResponse)
def get_entra_login_url(
    redirect_uri: str,
    tenant_id: str | None = None,
) -> Any:
    """Get Microsoft login URL for frontend redirect."""
    if not settings.azure_enabled:
        raise HTTPException(
            status_code=400, detail="Microsoft Entra authentication is not configured"
        )

    entra_client = EntraAuthClient()
    login_url = entra_client.get_login_url(redirect_uri, tenant_id)
    return EntraLoginUrlResponse(login_url=login_url)


@router.get("/config")
def get_entra_config() -> dict[str, Any]:
    """Return Entra configuration for the frontend (public info only)."""
    authority = None
    if settings.azure_enabled:
        authority = EntraAuthClient().get_authority()

    return {
        "enabled": settings.azure_enabled,
        "client_id": settings.AZURE_CLIENT_ID if settings.azure_enabled else None,
        "tenant_id": settings.AZURE_TENANT_ID if settings.azure_enabled else None,
        "authority": authority,
    }


# --- Tenant Management (admin only, for multi-tenant) ---

tenant_router = APIRouter(prefix="/tenants", tags=["tenants"])


@tenant_router.get("/", response_model=MicrosoftTenantsPublic)
def list_tenants(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """List all configured Microsoft tenants. Requires superuser."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough privileges")
    count_stmt = select(MicrosoftTenant)
    tenants = session.exec(count_stmt.offset(skip).limit(limit)).all()
    count = session.exec(select(func.count()).select_from(MicrosoftTenant)).one()
    return MicrosoftTenantsPublic(
        data=[MicrosoftTenantPublic.model_validate(t) for t in tenants], count=count
    )


@tenant_router.post("/", response_model=MicrosoftTenantPublic)
def create_tenant(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    tenant_in: MicrosoftTenantCreate,
) -> Any:
    """Add a new Microsoft tenant. Requires superuser."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough privileges")

    existing = session.exec(
        select(MicrosoftTenant).where(MicrosoftTenant.tenant_id == tenant_in.tenant_id)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Tenant already exists")

    db_tenant = MicrosoftTenant.model_validate(
        tenant_in, update={"created_by": current_user.id}
    )
    session.add(db_tenant)
    session.commit()
    session.refresh(db_tenant)
    return db_tenant


@tenant_router.patch("/{tenant_id}", response_model=MicrosoftTenantPublic)
def update_tenant(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    tenant_id: str,
    tenant_in: MicrosoftTenantUpdate,
) -> Any:
    """Update a Microsoft tenant. Requires superuser."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough privileges")

    db_tenant = session.exec(
        select(MicrosoftTenant).where(MicrosoftTenant.tenant_id == tenant_id)
    ).first()
    if not db_tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    tenant_data = tenant_in.model_dump(exclude_unset=True)
    db_tenant.sqlmodel_update(tenant_data)
    session.add(db_tenant)
    session.commit()
    session.refresh(db_tenant)
    return db_tenant


@tenant_router.delete("/{tenant_id}", response_model=Message)
def delete_tenant(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    tenant_id: str,
) -> Any:
    """Delete a Microsoft tenant. Requires superuser."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough privileges")

    db_tenant = session.exec(
        select(MicrosoftTenant).where(MicrosoftTenant.tenant_id == tenant_id)
    ).first()
    if not db_tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    session.delete(db_tenant)
    session.commit()
    return Message(message="Tenant deleted successfully")
