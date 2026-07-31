"""Private development-only endpoints for creating test data."""

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from backend.api.deps import SessionDep, SuperUserDep
from backend.core.auth.security import get_password_hash
from backend.models import (
    User,
    UserPublic,
)

router = APIRouter(tags=["private"], prefix="/private")


class PrivateUserCreate(BaseModel):
    """Schema for creating a private user in development."""

    email: str
    password: str
    full_name: str
    is_verified: bool = False


@router.post("/users/", response_model=UserPublic)
def create_user(
    user_in: PrivateUserCreate,
    session: SessionDep,
    _superuser: SuperUserDep,
) -> Any:
    """Create a new private user for local development (superuser only)."""
    user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=get_password_hash(user_in.password),
    )

    session.add(user)
    session.commit()

    return user
