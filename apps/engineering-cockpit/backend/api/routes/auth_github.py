"""GitHub OAuth authentication endpoints."""

import logging
from datetime import timedelta
from typing import Any

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel
from sqlmodel import select

from backend.api.deps import SessionDep
from backend.core.auth import security
from backend.core.auth.github import GitHubAuthClient
from backend.core.config import settings
from backend.models import Token, User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth/github", tags=["auth-github"])


class GitHubLoginRequest(BaseModel):
    """Request body for GitHub OAuth login."""

    access_token: str


class GitHubExchangeCodeRequest(BaseModel):
    """Request body for exchanging GitHub authorization code."""

    code: str


class GitHubConfigResponse(BaseModel):
    """Response schema containing GitHub OAuth configuration."""

    enabled: bool
    client_id: str | None = None


@router.post("/login", response_model=Token)
def github_login(
    request: GitHubLoginRequest,
    response: Response,
    session: SessionDep,
) -> Any:
    """
    Authenticate via GitHub OAuth.

    Accepts a GitHub access token (obtained via the GitHub OAuth flow
    on the frontend), validates it, fetches user info,
    and returns an application JWT.

    Args:
        request: GitHubLoginRequest containing the GitHub access token
        session: Database session

    Returns:
        Token with the application JWT for authenticated requests

    Raises:
        HTTPException: If GitHub auth is not configured or token validation fails
    """
    if not settings.github_enabled:
        raise HTTPException(
            status_code=400, detail="GitHub authentication is not configured"
        )

    github_client = GitHubAuthClient()

    try:
        # Validate token and get user info from GitHub
        user_info = github_client.validate_token(request.access_token)

        if not user_info:
            raise HTTPException(
                status_code=400, detail="Invalid or expired GitHub token"
            )
    except Exception as err:
        raise HTTPException(
            status_code=400, detail="Failed to validate GitHub token"
        ) from err

    github_user_id: int = user_info.id
    github_username: str = user_info.login

    # Require a verified email from the GitHub emails endpoint.
    email = github_client.get_user_email(request.access_token)

    if not email:
        raise HTTPException(
            status_code=400,
            detail="Could not retrieve a verified email from GitHub account. "
            "Please ensure your GitHub account has a verified primary email address.",
        )

    # Find or create user
    # First, try to find by github_id (existing GitHub login)
    db_user = session.exec(select(User).where(User.github_id == github_user_id)).first()

    # If not found by github_id, try by email (account linking)
    if not db_user:
        db_user = session.exec(select(User).where(User.email == email)).first()
        if db_user:
            # Link GitHub account to existing user
            db_user.github_id = github_user_id
            db_user.github_username = github_username
            session.add(db_user)
        else:
            # Create new user
            full_name = user_info.name or github_username

            db_user = User(
                email=email,
                full_name=full_name,
                github_id=github_user_id,
                github_username=github_username,
                is_active=True,
                is_superuser=False,
                hashed_password="",  # OAuth users don't have passwords
            )
            session.add(db_user)
    else:
        # Update user info from GitHub on each login
        db_user.github_username = github_username
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


@router.get("/config", response_model=GitHubConfigResponse)
def get_github_config() -> GitHubConfigResponse:
    """
    Return GitHub OAuth configuration for the frontend (public info only).

    The frontend uses this to determine if GitHub login is available
    and to get the GitHub Client ID for the OAuth flow.

    Returns:
        GitHubConfigResponse with enabled status and client_id if available
    """
    return GitHubConfigResponse(
        enabled=settings.github_enabled,
        client_id=settings.GITHUB_CLIENT_ID if settings.github_enabled else None,
    )


@router.post("/exchange-code", response_model=Token)
def exchange_code_for_token(
    request: GitHubExchangeCodeRequest,
    response: Response,
    session: SessionDep,
) -> Any:
    """
    Exchange GitHub authorization code for access token and authenticate.

    This endpoint is called by the frontend's GitHub OAuth callback handler
    to exchange the authorization code for an access token, then log in.

    Args:
        request: GitHubExchangeCodeRequest containing the authorization code
        session: Database session

    Returns:
        Token with the application JWT for authenticated requests

    Raises:
        HTTPException: If code exchange or authentication fails
    """
    if not settings.github_enabled:
        raise HTTPException(
            status_code=400, detail="GitHub authentication is not configured"
        )

    github_client = GitHubAuthClient()

    try:
        # Exchange authorization code for access token
        # The redirect_uri must match what was registered in GitHub OAuth settings
        redirect_uri = f"{settings.FRONTEND_HOST}/auth/github/callback"
        logger.info(
            f"Exchanging GitHub code for token with redirect_uri: {redirect_uri}"
        )

        access_token = github_client.get_access_token(request.code, redirect_uri)

        if not access_token:
            logger.error("Failed to get access token from GitHub")
            raise HTTPException(
                status_code=400, detail="Failed to exchange code for access token"
            )

        # Now authenticate using the access token
        user_info = github_client.validate_token(access_token)

        if not user_info:
            logger.error("Failed to validate GitHub token")
            raise HTTPException(
                status_code=400, detail="Invalid or expired GitHub token"
            )
    except HTTPException:
        raise
    except Exception as err:
        logger.error(f"GitHub authentication error: {err}")
        raise HTTPException(
            status_code=400, detail="Failed to authenticate with GitHub"
        ) from err

    github_user_id: int = user_info.id
    github_username: str = user_info.login

    # Require a verified email from the GitHub emails endpoint.
    email = github_client.get_user_email(access_token)

    if not email:
        raise HTTPException(
            status_code=400,
            detail="Could not retrieve a verified email from GitHub account. "
            "Please ensure your GitHub account has a verified primary email address.",
        )

    # Find or create user (same logic as /login endpoint)
    db_user = session.exec(select(User).where(User.github_id == github_user_id)).first()

    if not db_user:
        db_user = session.exec(select(User).where(User.email == email)).first()
        if db_user:
            db_user.github_id = github_user_id
            db_user.github_username = github_username
            session.add(db_user)
        else:
            full_name = user_info.name or github_username
            db_user = User(
                email=email,
                full_name=full_name,
                github_id=github_user_id,
                github_username=github_username,
                is_active=True,
                is_superuser=False,
                hashed_password="",
            )
            session.add(db_user)
    else:
        db_user.github_username = github_username
        if user_info.name:
            db_user.full_name = user_info.name
        session.add(db_user)

    session.commit()
    session.refresh(db_user)

    if not db_user.is_active:
        raise HTTPException(status_code=400, detail="User account is inactive")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        db_user.id, expires_delta=access_token_expires
    )
    security.set_auth_cookies(response, access_token)
    return Token(access_token=access_token)
