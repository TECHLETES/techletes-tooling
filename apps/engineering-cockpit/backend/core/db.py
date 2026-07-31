"""Database engine and initialization helpers."""

from sqlalchemy import delete
from sqlalchemy.engine import Engine
from sqlmodel import Session, col, create_engine, select

from backend import crud
from backend.core.config import settings
from backend.core.constants import constants
from backend.core.rbac import DEFAULT_PERMISSIONS, DEFAULT_SYSTEM_ROLES, RoleDefinition
from backend.models import Permission, RolePermission, User, UserCreate

engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))


def get_engine() -> Engine:
    """Get the database engine. Can be overridden in tests."""
    return engine


# make sure all SQLModel models are imported (backend.models) before initializing DB
# otherwise, SQLModel might fail to initialize relationships properly
# for more details: https://github.com/fastapi/full-stack-fastapi-template/issues/28


def init_db(session: Session) -> None:
    """Initialize the database with the first superuser and RBAC defaults."""
    # Tables should be created with Alembic migrations
    # But if you don't want to use migrations, create
    # the tables un-commenting the next lines
    # from sqlmodel import SQLModel

    # This works because the models are already imported and registered from backend.models
    # SQLModel.metadata.create_all(engine)

    user: User | None = session.exec(
        select(User).where(User.email == settings.FIRST_SUPERUSER)
    ).first()
    if user is None:
        user_in = UserCreate(
            email=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            is_superuser=True,
        )
        user = crud.create_user(session=session, user_create=user_in)

    _seed_rbac(session)


def _seed_rbac(
    session: Session,
    role_definitions: dict[str, RoleDefinition] | None = None,
) -> None:
    """Synchronize discovered permissions and system roles into the database."""
    from backend.crud_rbac import (
        add_permission_to_role,
        create_permission,
        create_role,
        delete_permission,
        get_permission_by_name,
        get_role_by_name,
        update_permission,
    )
    from backend.models import PermissionCreate, PermissionUpdate, RoleCreate

    role_definitions = role_definitions or DEFAULT_SYSTEM_ROLES

    desired_permissions = {
        perm_def["name"]: perm_def
        for perms in DEFAULT_PERMISSIONS.values()
        for perm_def in perms
    }
    existing_permissions = {
        permission.name: permission
        for permission in session.exec(select(Permission)).all()
    }

    # Create or update permissions from discovered usage.
    for permission_name, perm_def in desired_permissions.items():
        existing = existing_permissions.get(permission_name)
        if not existing:
            create_permission(
                session=session,
                permission_in=PermissionCreate(
                    name=perm_def["name"],
                    resource=perm_def["resource"],
                    description=perm_def.get("display", ""),
                ),
            )
            continue

        desired_description = perm_def.get("display", "")
        if (
            existing.resource != perm_def["resource"]
            or existing.description != desired_description
        ):
            update_permission(
                session=session,
                db_permission=existing,
                permission_in=PermissionUpdate(
                    resource=perm_def["resource"],
                    description=desired_description,
                ),
            )

    # Remove permissions no longer referenced in code.
    stale_permission_names = set(existing_permissions) - set(desired_permissions)
    for permission_name in stale_permission_names:
        stale_permission = existing_permissions[permission_name]
        session.exec(
            delete(RolePermission).where(
                col(RolePermission.permission_id) == stale_permission.id
            )
        )
        session.commit()
        delete_permission(session=session, permission_id=stale_permission.id)

    # Create and update system roles with their permissions.
    for role_name, role_def in role_definitions.items():
        existing_role = get_role_by_name(session=session, name=role_name)

        # For super_admin role, always assign ALL permissions
        if role_name == constants.roles.SUPER_ADMIN:
            desired_permission_ids = {
                perm.id for perm in session.exec(select(Permission)).all()
            }
        else:
            desired_permission_ids = {
                perm.id
                for perm_name in role_def["permissions"]
                if (perm := get_permission_by_name(session=session, name=perm_name))
            }

        if not existing_role:
            role = create_role(
                session=session,
                role_in=RoleCreate(
                    name=role_name,
                    description=role_def["description"],
                    permission_ids=[],
                ),
                is_system=True,
            )
            for permission_id in desired_permission_ids:
                perm = session.get(Permission, permission_id)
                if perm:
                    add_permission_to_role(
                        session=session, role_id=role.id, permission_id=perm.id
                    )
            continue

        existing_permission_ids = {
            permission.id for permission in existing_role.permissions
        }
        role_updated = False

        if existing_role.description != role_def["description"]:
            existing_role.description = role_def["description"]
            role_updated = True
        if not existing_role.is_system:
            existing_role.is_system = True
            role_updated = True
        if role_updated:
            session.add(existing_role)
            session.commit()
            session.refresh(existing_role)

        permissions_to_remove = existing_permission_ids - desired_permission_ids
        if permissions_to_remove:
            session.exec(
                delete(RolePermission).where(
                    col(RolePermission.role_id) == existing_role.id,
                    col(RolePermission.permission_id).in_(permissions_to_remove),
                )
            )
            session.commit()

        for permission_id in desired_permission_ids - existing_permission_ids:
            add_permission_to_role(
                session=session,
                role_id=existing_role.id,
                permission_id=permission_id,
            )
