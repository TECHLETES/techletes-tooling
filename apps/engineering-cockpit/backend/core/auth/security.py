"""Security utilities for password hashing and JWT token handling."""

from datetime import UTC, datetime, timedelta
from typing import Any, cast

import jwt
from fastapi import Response
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
from pwdlib.hashers.bcrypt import BcryptHasher

from backend.core.config import settings

password_hash = PasswordHash(
    (
        Argon2Hasher(),
        BcryptHasher(),
    )
)


ALGORITHM = "HS256"
SESSION_COOKIE_NAME = "access_token"
SESSION_STATE_COOKIE_NAME = "session_present"


def create_access_token(subject: str | Any, expires_delta: timedelta) -> str:
    """Create a JWT access token for the given subject."""
    expire = datetime.now(UTC) + expires_delta
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = cast(
        str, jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    )
    return encoded_jwt


def verify_password(
    plain_password: str, hashed_password: str
) -> tuple[bool, str | None]:
    """Verify a password against the stored hash and return any updated hash."""
    return cast(
        tuple[bool, str | None],
        password_hash.verify_and_update(plain_password, hashed_password),
    )


def get_password_hash(password: str) -> str:
    """Hash a plaintext password for storage."""
    return cast(str, password_hash.hash(password))


def set_auth_cookies(response: Response, token: str) -> None:
    """Set the authenticated session cookies on the response."""
    max_age = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    secure = settings.ENVIRONMENT != "local"
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        max_age=max_age,
        path="/",
        samesite="lax",
        secure=secure,
    )
    response.set_cookie(
        key=SESSION_STATE_COOKIE_NAME,
        value="1",
        httponly=False,
        max_age=max_age,
        path="/",
        samesite="lax",
        secure=secure,
    )


def clear_auth_cookies(response: Response) -> None:
    """Clear the authenticated session cookies on the response."""
    secure = settings.ENVIRONMENT != "local"
    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        path="/",
        samesite="lax",
        secure=secure,
    )
    response.delete_cookie(
        key=SESSION_STATE_COOKIE_NAME,
        path="/",
        samesite="lax",
        secure=secure,
    )
