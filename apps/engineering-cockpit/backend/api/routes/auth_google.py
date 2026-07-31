"""Google OAuth authentication endpoints."""

from datetime import timedelta
from typing import Any

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel
from sqlmodel import select

from backend.api.deps import SessionDep
from backend.core.auth import security
from backend.core.auth.google import GoogleAuthClient
from backend.core.config import settings
from backend.models import Token, User

router = APIRouter(prefix="/auth/google", tags=["auth-google"])


class GoogleLoginRequest(BaseModel):
    """Request body for Google OAuth login."""

    access_token: str


class GoogleExchangeCodeRequest(BaseModel):
    """Request body for exchanging a Google authorization code."""

    code: str


class GoogleConfigResponse(BaseModel):
    """Response schema containing Google OAuth configuration."""

    enabled: bool
    client_id: str | None = None


@router.post("/login", response_model=Token)
def google_login(
    request: GoogleLoginRequest,
    response: Response,
    session: SessionDep,
) -> Any:
    """
    Authenticate via Google OAuth.

    Accepts a Google access token (obtained via the Google Sign-In
    library on the frontend), validates it, fetches user info,
    and returns an application JWT.

    Args:
        request: GoogleLoginRequest containing the Google access token
        session: Database session

    Returns:
        Token with the application JWT for authenticated requests

    Raises:
        HTTPException: If Google auth is not configured or token validation fails
    """
    if not settings.google_enabled:
        raise HTTPException(
            status_code=400, detail="Google authentication is not configured"
        )

    google_client = GoogleAuthClient()

    try:
        # Validate token and get user info from Google
        user_info = google_client.validate_token(request.access_token)

        if not user_info:
            raise HTTPException(
                status_code=400, detail="Invalid or expired Google token"
            )
    except Exception as err:
        raise HTTPException(
            status_code=400, detail="Failed to validate Google token"
        ) from err

    if not user_info.email:
        raise HTTPException(
            status_code=400, detail="Could not retrieve email from Google account"
        )

    if not user_info.email_verified:
        raise HTTPException(
            status_code=400,
            detail="Google email is not verified. "
            "Please verify your email in Google.",
        )

    google_user_id: str = user_info.sub

    # Find or create user
    # First, try to find by google_id (existing Google login)
    db_user = session.exec(select(User).where(User.google_id == google_user_id)).first()

    # If not found by google_id, try by email (account linking)
    if not db_user:
        db_user = session.exec(
            select(User).where(User.email == user_info.email)
        ).first()
        if db_user:
            # Link Google account to existing user
            db_user.google_id = google_user_id
            db_user.google_email = user_info.email
            session.add(db_user)
        else:
            # Create new user
            # Use full_name from Google if available, otherwise construct from parts
            full_name = user_info.name
            if not full_name and user_info.given_name:
                parts = [user_info.given_name]
                if user_info.family_name:
                    parts.append(user_info.family_name)
                full_name = " ".join(parts)

            db_user = User(
                email=user_info.email,
                full_name=full_name,
                google_id=google_user_id,
                google_email=user_info.email,
                is_active=True,
                is_superuser=False,
                hashed_password="",  # OAuth users don't have passwords
            )
            session.add(db_user)
    else:
        # Update user info from Google on each login
        db_user.google_email = user_info.email
        if user_info.name:
            db_user.full_name = user_info.name
        session.add(db_user)

    session.commit()
    session.refresh(db_user)

    if not db_user.is_active:
        raise HTTPException(status_code=400, detail="User account is inactive")

    # Create JWT token for the application
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        db_user.id, expires_delta=access_token_expires
    )
    security.set_auth_cookies(response, access_token)
    return Token(access_token=access_token)


@router.post("/exchange-code", response_model=Token)
def exchange_code_for_token(
    request: GoogleExchangeCodeRequest,
    response: Response,
    session: SessionDep,
) -> Any:
    """Exchange a Google authorization code and authenticate."""
    if not settings.google_enabled:
        raise HTTPException(
            status_code=400, detail="Google authentication is not configured"
        )

    google_client = GoogleAuthClient()
    access_token = google_client.exchange_code_for_token(request.code)
    if not access_token:
        raise HTTPException(
            status_code=400, detail="Failed to exchange code for access token"
        )

    return google_login(
        request=GoogleLoginRequest(access_token=access_token),
        response=response,
        session=session,
    )


@router.get("/config", response_model=GoogleConfigResponse)
def get_google_config() -> GoogleConfigResponse:
    """
    Return Google OAuth configuration for the frontend (public info only).

    Returns config with enabled flag and client ID (no secret).
    """
    return GoogleConfigResponse(
        enabled=settings.google_enabled,
        client_id=settings.GOOGLE_CLIENT_ID if settings.google_enabled else None,
    )
