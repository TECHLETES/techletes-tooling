"""User management endpoints for the backend API."""

import mimetypes
import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import selectinload
from sqlmodel import col, func, select

from backend import crud
from backend.api.deps import CurrentUser, SessionDep, permission_dep
from backend.core.auth.security import get_password_hash, verify_password
from backend.core.config import settings
from backend.core.storage.backend import build_storage_key, get_storage
from backend.models import (
    Message,
    UpdatePassword,
    User,
    UserCreate,
    UserPublic,
    UserRegister,
    UsersPublic,
    UserUpdate,
    UserUpdateMe,
)
from backend.utils.utils import (
    generate_password_reset_token,
    generate_reset_password_email,
    send_email,
)

router = APIRouter(prefix="/users", tags=["users"])
MAX_AVATAR_BYTES = 5 * 1024 * 1024
ALLOWED_AVATAR_CONTENT_TYPES = {"image/jpeg", "image/png"}


@router.get(
    "/",
    dependencies=permission_dep("users:read"),
    response_model=UsersPublic,
)
def read_users(session: SessionDep, skip: int = 0, limit: int = 100) -> Any:
    """Retrieve users."""
    count_statement = select(func.count()).select_from(User)
    count = session.exec(count_statement).one()

    statement = (
        select(User)
        .options(selectinload(User.roles))
        .order_by(col(User.created_at).desc())
        .offset(skip)
        .limit(limit)
    )
    users = session.exec(statement).all()

    return UsersPublic(
        data=[UserPublic.model_validate(user) for user in users], count=count
    )


@router.post(
    "/",
    dependencies=permission_dep("users:create"),
    response_model=UserPublic,
)
def create_user(*, session: SessionDep, user_in: UserCreate) -> Any:
    """Create new user."""
    user = crud.get_user_by_email(session=session, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )

    user = crud.create_user(session=session, user_create=user_in)
    if settings.emails_enabled and user_in.email:
        password_reset_token = generate_password_reset_token(email=user_in.email)
        email_data = generate_reset_password_email(
            email_to=user_in.email,
            email=user_in.email,
            token=password_reset_token,
        )
        send_email(
            email_to=user_in.email,
            subject=email_data.subject,
            html_content=email_data.html_content,
        )
    return user


@router.patch("/me", response_model=UserPublic)
def update_user_me(
    *, session: SessionDep, user_in: UserUpdateMe, current_user: CurrentUser
) -> Any:
    """Update own user."""
    if user_in.email:
        existing_user = crud.get_user_by_email(session=session, email=user_in.email)
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=409, detail="User with this email already exists"
            )
    user_data = user_in.model_dump(exclude_unset=True)
    current_user.sqlmodel_update(user_data)
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    return current_user


@router.patch("/me/password", response_model=Message)
def update_password_me(
    *, session: SessionDep, body: UpdatePassword, current_user: CurrentUser
) -> Any:
    """Update own password."""
    if current_user.azure_user_id:
        raise HTTPException(
            status_code=400,
            detail="Password change is not available for Microsoft Entra managed accounts",
        )
    verified, _ = verify_password(body.current_password, current_user.hashed_password)
    if not verified:
        raise HTTPException(status_code=400, detail="Incorrect password")
    if body.current_password == body.new_password:
        raise HTTPException(
            status_code=400, detail="New password cannot be the same as the current one"
        )
    hashed_password = get_password_hash(body.new_password)
    current_user.hashed_password = hashed_password
    session.add(current_user)
    session.commit()
    return Message(message="Password updated successfully")


@router.post("/me/avatar", response_model=UserPublic)
def upload_user_avatar(
    *, session: SessionDep, current_user: CurrentUser, file: UploadFile
) -> Any:
    """Upload or replace the current user's avatar image."""
    if file.content_type not in ALLOWED_AVATAR_CONTENT_TYPES:
        raise HTTPException(
            status_code=415,
            detail="Only image/jpeg and image/png are allowed",
        )

    data = file.file.read(MAX_AVATAR_BYTES + 1)
    if len(data) > MAX_AVATAR_BYTES:
        raise HTTPException(
            status_code=413,
            detail="Avatar exceeds maximum size of 5 MB",
        )

    storage = get_storage()
    if current_user.avatar_url:
        storage.delete(current_user.avatar_url)

    filename = file.filename or "avatar"
    storage_key = build_storage_key(current_user.id, filename)
    storage.save(data, storage_key)

    current_user.avatar_url = storage_key
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    return current_user


@router.get("/me/avatar/download")
def download_user_avatar(*, current_user: CurrentUser) -> Response:
    """Stream the current user's avatar image bytes to the client."""
    storage_key = current_user.avatar_url
    if not storage_key:
        raise HTTPException(status_code=404, detail="Avatar not found")

    storage = get_storage()
    try:
        data = storage.open(storage_key)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Avatar not found") from exc

    media_type = (
        mimetypes.guess_type(Path(storage_key).name)[0] or "application/octet-stream"
    )
    return Response(
        content=data,
        media_type=media_type,
        headers={"Content-Length": str(len(data))},
    )


@router.delete("/me/avatar", response_model=UserPublic)
def delete_user_avatar(*, session: SessionDep, current_user: CurrentUser) -> Any:
    """Delete the current user's avatar image."""
    if current_user.avatar_url:
        storage = get_storage()
        storage.delete(current_user.avatar_url)
        current_user.avatar_url = None
        session.add(current_user)
        session.commit()
        session.refresh(current_user)
    return current_user


@router.get("/me", response_model=UserPublic)
def read_user_me(current_user: CurrentUser) -> Any:
    """Get current user."""
    return current_user


@router.delete("/me", response_model=Message)
def delete_user_me(session: SessionDep, current_user: CurrentUser) -> Any:
    """Delete own user."""
    if current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="Super users are not allowed to delete themselves"
        )
    session.delete(current_user)
    session.commit()
    return Message(message="User deleted successfully")


@router.post("/signup", response_model=UserPublic)
def register_user(session: SessionDep, user_in: UserRegister) -> Any:
    """Create a new user without authentication."""
    if not settings.SIGNUP_ENABLED:
        raise HTTPException(
            status_code=403,
            detail="User registration is currently disabled.",
        )
    user = crud.get_user_by_email(session=session, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system",
        )
    user_create = UserCreate.model_validate(user_in)
    user = crud.create_user(session=session, user_create=user_create)
    return user


@router.get("/{user_id}", response_model=UserPublic)
def read_user_by_id(
    user_id: uuid.UUID, session: SessionDep, current_user: CurrentUser
) -> Any:
    """Get a specific user by ID."""
    user = session.exec(
        select(User).options(selectinload(User.roles)).where(User.id == user_id)
    ).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    # Users can always read themselves
    if user.id == current_user.id:
        return user
    # Otherwise, require users:read permission
    from backend.crud_rbac import user_has_permission

    if not user_has_permission(
        session=session, user_id=current_user.id, permission_name="users:read"
    ):
        raise HTTPException(
            status_code=403,
            detail="The user doesn't have enough privileges",
        )
    return user


@router.patch(
    "/{user_id}",
    dependencies=permission_dep("users:update"),
    response_model=UserPublic,
)
def update_user(
    *,
    session: SessionDep,
    user_id: uuid.UUID,
    user_in: UserUpdate,
) -> Any:
    """Update a user."""
    db_user = session.get(User, user_id)
    if not db_user:
        raise HTTPException(
            status_code=404,
            detail="The user with this id does not exist in the system",
        )
    if user_in.email:
        existing_user = crud.get_user_by_email(session=session, email=user_in.email)
        if existing_user and existing_user.id != user_id:
            raise HTTPException(
                status_code=409, detail="User with this email already exists"
            )

    db_user = crud.update_user(session=session, db_user=db_user, user_in=user_in)
    return db_user


@router.delete("/{user_id}", dependencies=permission_dep("users:delete"))
def delete_user(
    session: SessionDep, current_user: CurrentUser, user_id: uuid.UUID
) -> Message:
    """Delete a user."""
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user == current_user:
        raise HTTPException(
            status_code=403, detail="Super users are not allowed to delete themselves"
        )
    session.delete(user)
    session.commit()
    return Message(message="User deleted successfully")
