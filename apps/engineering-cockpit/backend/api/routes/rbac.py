"""RBAC endpoints for managing roles and permissions."""

import uuid
from typing import cast

from fastapi import APIRouter, HTTPException, Query
from sqlmodel import select

from backend.api.deps import CurrentUser, SessionDep, permission_dep
from backend.core.auth.entra import EntraAuthClient
from backend.core.config import settings
from backend.core.constants import constants
from backend.core.rbac import DEFAULT_PERMISSIONS, PermissionDefinition
from backend.crud_rbac import (
    add_permission_to_role,
    assign_role_to_user,
    create_permission,
    create_role,
    delete_permission,
    delete_role,
    get_all_permissions,
    get_all_roles,
    get_permission,
    get_role,
    get_user_permissions,
    get_user_roles,
    remove_permission_from_role,
    remove_role_from_user,
    update_permission,
    update_role,
)
from backend.models import (
    EntraAppRoleManifestEntry,
    EntraAppRoleManifestPublic,
    PermissionCreate,
    PermissionPublic,
    PermissionsPublic,
    PermissionUpdate,
    Role,
    RoleCreate,
    RolePublic,
    RolesPublic,
    RoleUpdate,
)

router = APIRouter(prefix="/rbac", tags=["rbac"])


def _normalize_entra_manifest_role_name(role_name: str) -> str:
    if role_name.casefold() == settings.AZURE_SUPERUSER_ROLE.casefold():
        return constants.roles.SUPER_ADMIN
    return role_name


def _fallback_entra_role_id(role_name: str) -> str:
    return str(
        uuid.uuid5(
            uuid.NAMESPACE_URL,
            f"{constants.entra.APP_ROLE_ID_NAMESPACE}/{role_name.casefold()}",
        )
    )


def _get_existing_entra_role_ids() -> dict[str, str]:
    if not settings.azure_enabled:
        return {}

    app_roles = EntraAuthClient().get_application_roles()
    existing_ids: dict[str, str] = {}
    for app_role in app_roles:
        role_name = app_role.get("value") or app_role.get("displayName")
        role_id = app_role.get("id")
        if isinstance(role_name, str) and isinstance(role_id, str):
            normalized_name = _normalize_entra_manifest_role_name(role_name)
            existing_ids[normalized_name.casefold()] = role_id
    return existing_ids


def _role_name_to_entra_value(name: str) -> str:
    """Convert role name to valid Entra app role value (identifier).

    Entra requires the value to be a valid identifier without spaces or special chars.
    Converts spaces to underscores and lowercases.
    """
    return name.replace(" ", "_").replace("-", "_").lower()


def _build_entra_manifest_export(roles: list[Role]) -> EntraAppRoleManifestPublic:
    """Export roles as Entra app role manifest entries.

    Uses entra_role_id field from the database to determine which roles already exist
    in Entra. Existing roles are marked as disabled so they can be updated.
    """
    app_roles = [
        EntraAppRoleManifestEntry(
            # Use the stored entra_role_id, or generate a deterministic fallback
            id=role.entra_role_id or _fallback_entra_role_id(role.name),
            description=role.description or f"{role.name} role",
            displayName=role.name,
            value=_role_name_to_entra_value(role.name),
            # Disable existing roles (those with entra_role_id set) so they can be updated
            isEnabled=not bool(role.entra_role_id),
        )
        for role in roles
    ]

    return EntraAppRoleManifestPublic(appRoles=app_roles)


# --- Permissions Endpoints ---


@router.get(
    "/permissions",
    response_model=PermissionsPublic,
    dependencies=permission_dep("rbac:view_permissions"),
)
def list_permissions(
    *,
    session: SessionDep,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
) -> PermissionsPublic:
    """List all permissions with pagination."""
    permissions, count = get_all_permissions(session=session, skip=skip, limit=limit)
    return PermissionsPublic(
        data=[PermissionPublic.model_validate(p) for p in permissions], count=count
    )


@router.get(
    "/permissions/{permission_id}",
    response_model=PermissionPublic,
    dependencies=permission_dep("rbac:view_permissions"),
)
def get_permission_endpoint(
    *, session: SessionDep, permission_id: uuid.UUID
) -> PermissionPublic:
    """Get permission by ID."""
    permission = get_permission(session=session, permission_id=permission_id)
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")
    return cast(PermissionPublic, PermissionPublic.model_validate(permission))


@router.post(
    "/permissions",
    response_model=PermissionPublic,
    dependencies=permission_dep("rbac:create_role"),
)
def create_permission_endpoint(
    *, session: SessionDep, permission_in: PermissionCreate
) -> PermissionPublic:
    """Create a new permission (requires rbac:create_role permission)."""
    permission = create_permission(session=session, permission_in=permission_in)
    return cast(PermissionPublic, PermissionPublic.model_validate(permission))


@router.patch(
    "/permissions/{permission_id}",
    response_model=PermissionPublic,
    dependencies=permission_dep("rbac:update_role"),
)
def update_permission_endpoint(
    *,
    session: SessionDep,
    permission_id: uuid.UUID,
    permission_in: PermissionUpdate,
) -> PermissionPublic:
    """Update a permission (requires rbac:update_role permission)."""
    permission = get_permission(session=session, permission_id=permission_id)
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")
    updated = update_permission(
        session=session, db_permission=permission, permission_in=permission_in
    )
    return cast(PermissionPublic, PermissionPublic.model_validate(updated))


@router.delete(
    "/permissions/{permission_id}",
    dependencies=permission_dep("rbac:delete_role"),
)
def delete_permission_endpoint(
    *, session: SessionDep, permission_id: uuid.UUID
) -> dict[str, str]:
    """Delete a permission (requires rbac:delete_role permission)."""
    if not delete_permission(session=session, permission_id=permission_id):
        raise HTTPException(status_code=404, detail="Permission not found")
    return {"message": "Permission deleted"}


# --- Roles Endpoints ---


@router.get(
    "/roles",
    response_model=RolesPublic,
    dependencies=permission_dep("rbac:view_roles"),
)
def list_roles(
    *,
    session: SessionDep,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
) -> RolesPublic:
    """List all roles with pagination."""
    roles, count = get_all_roles(session=session, skip=skip, limit=limit)
    return RolesPublic(
        data=[RolePublic.model_validate(r, from_attributes=True) for r in roles],
        count=count,
    )


@router.get(
    "/roles/entra-manifest",
    response_model=EntraAppRoleManifestPublic,
    dependencies=permission_dep("rbac:view_roles"),
)
def get_entra_app_role_manifest_endpoint(
    *, session: SessionDep
) -> EntraAppRoleManifestPublic:
    """Export current application roles as a Microsoft Entra appRoles manifest payload."""
    roles = list(session.exec(select(Role).order_by(Role.name)).all())
    return _build_entra_manifest_export(roles)


@router.get(
    "/roles/{role_id}",
    response_model=RolePublic,
    dependencies=permission_dep("rbac:view_roles"),
)
def get_role_endpoint(*, session: SessionDep, role_id: uuid.UUID) -> RolePublic:
    """Get role by ID."""
    role = get_role(session=session, role_id=role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return cast(RolePublic, RolePublic.model_validate(role, from_attributes=True))


@router.post(
    "/roles",
    response_model=RolePublic,
    dependencies=permission_dep("rbac:create_role"),
)
def create_role_endpoint(*, session: SessionDep, role_in: RoleCreate) -> RolePublic:
    """Create a new role (requires rbac:create_role permission)."""
    role = create_role(session=session, role_in=role_in)
    return cast(RolePublic, RolePublic.model_validate(role, from_attributes=True))


@router.patch(
    "/roles/{role_id}",
    response_model=RolePublic,
    dependencies=permission_dep("rbac:update_role"),
)
def update_role_endpoint(
    *,
    session: SessionDep,
    role_id: uuid.UUID,
    role_in: RoleUpdate,
) -> RolePublic:
    """Update a role (requires rbac:update_role permission)."""
    role = get_role(session=session, role_id=role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    try:
        updated = update_role(session=session, db_role=role, role_in=role_in)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return cast(RolePublic, RolePublic.model_validate(updated, from_attributes=True))


@router.delete(
    "/roles/{role_id}",
    dependencies=permission_dep("rbac:delete_role"),
)
def delete_role_endpoint(*, session: SessionDep, role_id: uuid.UUID) -> dict[str, str]:
    """Delete a role (requires rbac:delete_role permission)."""
    if not delete_role(session=session, role_id=role_id):
        raise HTTPException(
            status_code=404, detail="Role not found or cannot delete system role"
        )
    return {"message": "Role deleted"}


# --- Role-Permission Mapping ---


@router.post(
    "/roles/{role_id}/permissions/{permission_id}",
    dependencies=permission_dep("rbac:assign_permissions"),
)
def add_permission_to_role_endpoint(
    *,
    session: SessionDep,
    role_id: uuid.UUID,
    permission_id: uuid.UUID,
) -> dict[str, str]:
    """Add permission to role (requires rbac:assign_permissions permission)."""
    if not add_permission_to_role(
        session=session, role_id=role_id, permission_id=permission_id
    ):
        raise HTTPException(status_code=404, detail="Role or permission not found")
    return {"message": "Permission added to role"}


@router.delete(
    "/roles/{role_id}/permissions/{permission_id}",
    dependencies=permission_dep("rbac:assign_permissions"),
)
def remove_permission_from_role_endpoint(
    *,
    session: SessionDep,
    role_id: uuid.UUID,
    permission_id: uuid.UUID,
) -> dict[str, str]:
    """Remove permission from role (requires rbac:assign_permissions permission)."""
    if not remove_permission_from_role(
        session=session, role_id=role_id, permission_id=permission_id
    ):
        raise HTTPException(status_code=404, detail="Mapping not found")
    return {"message": "Permission removed from role"}


# --- User-Role Mapping ---


@router.post(
    "/users/{user_id}/roles/{role_id}",
    dependencies=permission_dep("rbac:manage_users"),
)
def assign_role_to_user_endpoint(
    *,
    session: SessionDep,
    user_id: uuid.UUID,
    role_id: uuid.UUID,
) -> dict[str, str]:
    """Assign role to user (requires rbac:manage_users permission)."""
    if not assign_role_to_user(session=session, user_id=user_id, role_id=role_id):
        raise HTTPException(status_code=404, detail="User or role not found")
    return {"message": "Role assigned to user"}


@router.delete(
    "/users/{user_id}/roles/{role_id}",
    dependencies=permission_dep("rbac:manage_users"),
)
def remove_role_from_user_endpoint(
    *,
    session: SessionDep,
    user_id: uuid.UUID,
    role_id: uuid.UUID,
) -> dict[str, str]:
    """Remove role from user (requires rbac:manage_users permission)."""
    if not remove_role_from_user(session=session, user_id=user_id, role_id=role_id):
        raise HTTPException(status_code=404, detail="Assignment not found")
    return {"message": "Role removed from user"}


@router.get(
    "/users/{user_id}/roles",
    response_model=RolesPublic,
)
def get_user_roles_endpoint(
    *, session: SessionDep, user_id: uuid.UUID, current_user: CurrentUser
) -> RolesPublic:
    """Get all roles for a user.

    Users can always view their own roles. Viewing other users' roles requires
    rbac:view_roles permission.
    """
    from backend.crud_rbac import user_has_permission

    # Users can always view their own roles
    if user_id != current_user.id:
        # Viewing another user's roles requires permission
        if not user_has_permission(
            session=session, user_id=current_user.id, permission_name="rbac:view_roles"
        ):
            raise HTTPException(
                status_code=403,
                detail="The user doesn't have enough privileges",
            )

    roles = get_user_roles(session=session, user_id=user_id)
    return RolesPublic(
        data=[RolePublic.model_validate(r, from_attributes=True) for r in roles],
        count=len(roles),
    )


@router.get(
    "/users/{user_id}/permissions",
    response_model=PermissionsPublic,
)
def get_user_permissions_endpoint(
    *, session: SessionDep, user_id: uuid.UUID, current_user: CurrentUser
) -> PermissionsPublic:
    """Get all permissions for a user (via their roles).

    Users can always view their own permissions. Viewing other users' permissions
    requires rbac:view_permissions permission.
    """
    from backend.crud_rbac import user_has_permission

    # Users can always view their own permissions
    if user_id != current_user.id:
        # Viewing another user's permissions requires permission
        if not user_has_permission(
            session=session,
            user_id=current_user.id,
            permission_name="rbac:view_permissions",
        ):
            raise HTTPException(
                status_code=403,
                detail="The user doesn't have enough privileges",
            )

    permissions = get_user_permissions(session=session, user_id=user_id)
    return PermissionsPublic(
        data=[PermissionPublic.model_validate(p) for p in permissions],
        count=len(permissions),
    )


# --- Permissions Catalog ---


@router.get("/permissions-catalog")
def get_permissions_catalog() -> dict[str, list[PermissionDefinition]]:
    """
    Get the catalog of available permissions in the application.

    This endpoint returns the predefined permissions that can be assigned to roles.
    Useful for UI to display what permissions are available.
    This is a public endpoint and does not require authentication.
    """
    return DEFAULT_PERMISSIONS
