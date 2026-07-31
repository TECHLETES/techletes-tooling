"""Dependency utilities for database sessions, authentication, and authorization."""

from collections.abc import Callable, Generator
from typing import Annotated, Any, cast

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError
from sqlmodel import Session

from backend.core.auth import security
from backend.core.config import settings
from backend.core.db import engine
from backend.crud_rbac import user_has_permission, user_has_role
from backend.models import TokenPayload, User

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token",
    auto_error=False,
)


def get_db() -> Generator[Session, None, None]:
    """Yield a database session for request-scoped dependencies."""
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_db)]
TokenDep = Annotated[str | None, Depends(reusable_oauth2)]


def get_current_user(
    session: SessionDep,
    request: Request,
    token: TokenDep,
) -> User | None:
    """Decode the JWT token and return the current authenticated user."""
    raw_token = token or request.cookies.get(security.SESSION_COOKIE_NAME)
    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    try:
        payload = jwt.decode(
            raw_token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (InvalidTokenError, ValidationError) as err:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        ) from err
    user = session.get(User, token_data.sub)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return cast(User, user)


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_current_active_superuser(current_user: CurrentUser) -> User:
    """Ensure the current user is a superuser."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    return current_user


SuperUserDep = Annotated[User, Depends(get_current_active_superuser)]


def require_role(role_name: str) -> Callable[..., User]:
    """
    Dependency factory to require a specific RBAC role.

    Usage:
        @router.get("/admin", dependencies=[Depends(require_role("admin"))])
        async def admin_only(): ...

        # Or as a typed parameter:
        async def admin_only(current_user: Annotated[User, Depends(require_role("admin"))]):
    """

    def check_role(current_user: CurrentUser, session: SessionDep) -> User:
        # Superusers bypass all role checks
        if current_user.is_superuser:
            return current_user

        if not user_has_role(
            session=session, user_id=current_user.id, role_name=role_name
        ):
            raise HTTPException(
                status_code=403,
                detail=f"User does not have required role: {role_name}",
            )
        return current_user

    return check_role


def require_permission(
    permission_name: str,
) -> Callable[[CurrentUser, SessionDep], User]:
    """
    Dependency factory to require a specific permission.

    Usage:
        @router.delete("/users/{user_id}", dependencies=[Depends(require_permission("users:delete"))])
        async def delete_user(): ...
    """

    def check_permission(current_user: CurrentUser, session: SessionDep) -> User:
        # Superusers bypass all permission checks
        if current_user.is_superuser:
            return current_user

        if not user_has_permission(
            session=session,
            user_id=current_user.id,
            permission_name=permission_name,
        ):
            raise HTTPException(
                status_code=403,
                detail=f"User does not have required permission: {permission_name}",
            )
        return current_user

    return check_permission


def permission_dep(permission_name: str) -> list[Any]:
    """
    Alias for require_permission to allow more concise usage.

    Usage:
        @router.delete("/reports/{report_id}", dependencies=[Depends(permission_dep("reports:download"))])
        async def download_report(): ...
    """
    return [Depends(require_permission(permission_name=permission_name))]


def require_any_role(*role_names: str) -> Callable[[CurrentUser, SessionDep], User]:
    """
    Dependency factory to require any of the specified roles.

    Usage:
        @router.get("/reports", dependencies=[Depends(require_any_role("admin", "editor"))])
        async def get_reports(): ...
    """

    def check_any_role(current_user: CurrentUser, session: SessionDep) -> User:
        # Superusers bypass all role checks
        if current_user.is_superuser:
            return current_user

        has_any = any(
            user_has_role(session=session, user_id=current_user.id, role_name=role)
            for role in role_names
        )
        if not has_any:
            raise HTTPException(
                status_code=403,
                detail=f"User does not have any of required roles: {', '.join(role_names)}",
            )
        return current_user

    return check_any_role


def require_all_permissions(
    *permission_names: str,
) -> Callable[[CurrentUser, SessionDep], User]:
    """
    Dependency factory to require all of the specified permissions.

    Usage:
        @router.post("/endpoint", dependencies=[Depends(require_all_permissions("users:create", "users:manage_roles"))])
        async def endpoint(): ...
    """

    def check_all_permissions(current_user: CurrentUser, session: SessionDep) -> User:
        # Superusers bypass all permission checks
        if current_user.is_superuser:
            return current_user

        missing = [
            perm
            for perm in permission_names
            if not user_has_permission(
                session=session, user_id=current_user.id, permission_name=perm
            )
        ]
        if missing:
            raise HTTPException(
                status_code=403,
                detail=f"User is missing required permissions: {', '.join(missing)}",
            )
        return current_user

    return check_all_permissions
