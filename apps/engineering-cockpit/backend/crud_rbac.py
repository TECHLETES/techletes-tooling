"""CRUD operations for RBAC (roles, permissions, role assignments)."""

import uuid
from typing import cast

from sqlalchemy import delete
from sqlmodel import Session, col, select

from backend.core.constants import constants
from backend.models import (
    Permission,
    PermissionCreate,
    PermissionUpdate,
    Role,
    RoleCreate,
    RolePermission,
    RoleUpdate,
    User,
    UserRole,
)

# --- Permission CRUD ---


def create_permission(
    *, session: Session, permission_in: PermissionCreate
) -> Permission:
    """Create a new permission."""
    db_permission = Permission.model_validate(permission_in)
    session.add(db_permission)
    session.commit()
    session.refresh(db_permission)
    return cast(Permission, db_permission)


def get_permission(*, session: Session, permission_id: uuid.UUID) -> Permission | None:
    """Get permission by ID."""
    return cast(
        Permission | None,
        session.exec(select(Permission).where(Permission.id == permission_id)).first(),
    )


def get_permission_by_name(*, session: Session, name: str) -> Permission | None:
    """Get permission by name."""
    return cast(
        Permission | None,
        session.exec(select(Permission).where(Permission.name == name)).first(),
    )


def get_all_permissions(
    *, session: Session, skip: int = 0, limit: int = 100
) -> tuple[list[Permission], int]:
    """Get all permissions with pagination."""
    count = session.exec(select(Permission)).all().__len__()
    permissions = list(session.exec(select(Permission).offset(skip).limit(limit)).all())
    return permissions, count


def update_permission(
    *,
    session: Session,
    db_permission: Permission,
    permission_in: PermissionUpdate,
) -> Permission:
    """Update a permission."""
    permission_data = permission_in.model_dump(exclude_unset=True)
    db_permission.sqlmodel_update(permission_data)
    session.add(db_permission)
    session.commit()
    session.refresh(db_permission)
    return db_permission


def delete_permission(*, session: Session, permission_id: uuid.UUID) -> bool:
    """Delete a permission."""
    db_permission = get_permission(session=session, permission_id=permission_id)
    if not db_permission:
        return False
    session.delete(db_permission)
    session.commit()
    return True


# --- Role CRUD ---


def create_role(
    *, session: Session, role_in: RoleCreate, is_system: bool = False
) -> Role:
    """Create a new role with optional permissions."""
    db_role = Role.model_validate(role_in, update={"is_system": is_system})
    session.add(db_role)
    session.flush()  # Get the ID without committing

    # Add permissions if provided
    if role_in.permission_ids:
        for permission_id in role_in.permission_ids:
            if get_permission(session=session, permission_id=permission_id):
                role_permission = RolePermission(
                    role_id=db_role.id, permission_id=permission_id
                )
                session.add(role_permission)

    session.commit()
    session.refresh(db_role)
    return cast(Role, db_role)


def get_role(*, session: Session, role_id: uuid.UUID) -> Role | None:
    """Get role by ID."""
    return cast(
        Role | None, session.exec(select(Role).where(Role.id == role_id)).first()
    )


def get_role_by_name(*, session: Session, name: str) -> Role | None:
    """Get role by name."""
    return cast(
        Role | None, session.exec(select(Role).where(Role.name == name)).first()
    )


def get_all_roles(
    *, session: Session, skip: int = 0, limit: int = 100
) -> tuple[list[Role], int]:
    """Get all roles with pagination."""
    count = session.exec(select(Role)).all().__len__()
    roles = list(session.exec(select(Role).offset(skip).limit(limit)).all())
    return roles, count


def update_role(*, session: Session, db_role: Role, role_in: RoleUpdate) -> Role:
    """Update a role and optionally update its permissions.

    IMPORTANT: Super admin role has restrictions:
    - Only the entra_role_id field can be updated
    - name, description, and permission_ids cannot be modified to protect system integrity
    """
    # Check if trying to update Super admin role
    if db_role.name == constants.roles.SUPER_ADMIN:
        # Allow Super admin update ONLY if only entra_role_id was explicitly set in the request
        # Use model_fields_set to check which fields were actually provided (not defaults)
        provided_fields = role_in.model_fields_set
        is_only_entra_id = provided_fields == {"entra_role_id"} or (
            provided_fields <= {"entra_role_id"} and "entra_role_id" in provided_fields
        )
        if not is_only_entra_id:
            raise ValueError(
                f"{constants.roles.SUPER_ADMIN} role can only have its Entra Role ID updated"
            )

    role_data = role_in.model_dump(exclude_unset=True, exclude={"permission_ids"})
    db_role.sqlmodel_update(role_data)

    # Update permissions if provided (skip for Super admin)
    if (
        role_in.permission_ids is not None
        and db_role.name != constants.roles.SUPER_ADMIN
    ):
        # Remove existing permissions
        to_delete = delete(RolePermission).where(
            col(RolePermission.role_id) == db_role.id
        )
        session.exec(to_delete)

        # Add new permissions
        for permission_id in role_in.permission_ids:
            if get_permission(session=session, permission_id=permission_id):
                role_permission = RolePermission(
                    role_id=db_role.id, permission_id=permission_id
                )
                session.add(role_permission)

    session.add(db_role)
    session.commit()
    session.refresh(db_role)
    return db_role


def delete_role(*, session: Session, role_id: uuid.UUID) -> bool:
    """Delete a role."""
    db_role = get_role(session=session, role_id=role_id)
    if not db_role:
        return False
    if db_role.is_system:
        return False  # Prevent deletion of system roles
    session.delete(db_role)
    session.commit()
    return True


# --- Role-Permission Mapping ---


def add_permission_to_role(
    *, session: Session, role_id: uuid.UUID, permission_id: uuid.UUID
) -> bool:
    """Add permission to role."""
    if not get_role(session=session, role_id=role_id):
        return False
    if not get_permission(session=session, permission_id=permission_id):
        return False

    # Check if already exists
    existing = session.exec(
        select(RolePermission).where(
            (RolePermission.role_id == role_id)
            & (RolePermission.permission_id == permission_id)
        )
    ).first()
    if existing:
        return True

    role_permission = RolePermission(role_id=role_id, permission_id=permission_id)
    session.add(role_permission)
    session.commit()
    return True


def remove_permission_from_role(
    *, session: Session, role_id: uuid.UUID, permission_id: uuid.UUID
) -> bool:
    """Remove permission from role."""
    role_permission = session.exec(
        select(RolePermission).where(
            (RolePermission.role_id == role_id)
            & (RolePermission.permission_id == permission_id)
        )
    ).first()
    if not role_permission:
        return False
    session.delete(role_permission)
    session.commit()
    return True


# --- User-Role Mapping ---


def assign_role_to_user(
    *, session: Session, user_id: uuid.UUID, role_id: uuid.UUID
) -> bool:
    """Assign role to user."""
    if not session.exec(select(User).where(User.id == user_id)).first():
        return False
    if not get_role(session=session, role_id=role_id):
        return False

    # Check if already assigned
    existing = session.exec(
        select(UserRole).where(
            (UserRole.user_id == user_id) & (UserRole.role_id == role_id)
        )
    ).first()
    if existing:
        return True

    user_role = UserRole(user_id=user_id, role_id=role_id)
    session.add(user_role)
    session.commit()
    return True


def remove_role_from_user(
    *, session: Session, user_id: uuid.UUID, role_id: uuid.UUID
) -> bool:
    """Remove role from user."""
    user_role = session.exec(
        select(UserRole).where(
            (UserRole.user_id == user_id) & (UserRole.role_id == role_id)
        )
    ).first()
    if not user_role:
        return False
    session.delete(user_role)
    session.commit()
    return True


def get_user_roles(*, session: Session, user_id: uuid.UUID) -> list[Role]:
    """Get all roles for a user."""
    user = session.exec(select(User).where(User.id == user_id)).first()
    if not user:
        return []

    roles = list(user.roles or [])
    if user.is_superuser:
        super_admin_role = get_role_by_name(
            session=session, name=constants.roles.SUPER_ADMIN
        )
        if super_admin_role and all(role.id != super_admin_role.id for role in roles):
            roles.append(super_admin_role)

    return roles


def get_user_permissions(*, session: Session, user_id: uuid.UUID) -> list[Permission]:
    """Get all permissions for a user (via their roles)."""
    roles = get_user_roles(session=session, user_id=user_id)
    seen_ids: set[uuid.UUID] = set()
    permissions: list[Permission] = []
    for role in roles:
        for perm in role.permissions or []:
            if perm.id not in seen_ids:
                seen_ids.add(perm.id)
                permissions.append(perm)
    return permissions


def get_users_with_role(*, session: Session, role_id: uuid.UUID) -> list[User]:
    """Get all users with a specific role."""
    role = get_role(session=session, role_id=role_id)
    if not role:
        return []
    return role.users or []


def user_has_role(*, session: Session, user_id: uuid.UUID, role_name: str) -> bool:
    """Check if user has a specific role by name."""
    roles = get_user_roles(session=session, user_id=user_id)
    return any(role.name == role_name for role in roles)


def user_has_permission(
    *, session: Session, user_id: uuid.UUID, permission_name: str
) -> bool:
    """Check if user has a specific permission."""
    # Super admins have all permissions
    if user_has_role(
        session=session,
        user_id=user_id,
        role_name=constants.roles.SUPER_ADMIN,
    ):
        return True

    permissions = get_user_permissions(session=session, user_id=user_id)
    return any(perm.name == permission_name for perm in permissions)


def is_user_super_admin(*, session: Session, user_id: uuid.UUID) -> bool:
    """Check if user has the Super admin role."""
    return user_has_role(
        session=session,
        user_id=user_id,
        role_name=constants.roles.SUPER_ADMIN,
    )
