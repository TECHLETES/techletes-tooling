"""GitHub OAuth authentication client utilities."""

import logging

import httpx
from pydantic import BaseModel

from backend.core.config import settings

logger = logging.getLogger(__name__)


class GitHubTokenInfo(BaseModel):
    """User information from GitHub OAuth token."""

    id: int  # GitHub user ID
    login: str  # GitHub username
    email: str | None = None
    name: str | None = None
    avatar_url: str | None = None


class GitHubAuthClient:
    """Handle GitHub OAuth authentication."""

    GITHUB_API_BASE_URL = "https://api.github.com"
    GITHUB_USER_ENDPOINT = f"{GITHUB_API_BASE_URL}/user"

    def __init__(self) -> None:
        """Initialize the GitHub auth client with configuration values."""
        self.client_id = settings.GITHUB_CLIENT_ID
        self.client_secret = settings.GITHUB_CLIENT_SECRET

    def get_access_token(self, code: str, redirect_uri: str) -> str | None:
        """
        Exchange authorization code for access token.

        Args:
            code: The authorization code from GitHub OAuth callback
            redirect_uri: The redirect URI used in the authorization request

        Returns:
            Access token if successful, None if failed.
        """
        try:
            with httpx.Client() as client:
                response = client.post(
                    "https://github.com/login/oauth/access_token",
                    data={
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "code": code,
                        "redirect_uri": redirect_uri,
                    },
                    headers={"Accept": "application/json"},
                    timeout=10.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    token: str | None = data.get("access_token")
                    return token
                else:
                    logger.error(
                        "Failed to get GitHub access token: %s %s",
                        response.status_code,
                        response.text,
                    )
                    return None

        except httpx.RequestError as e:
            logger.error("Failed to exchange GitHub code for token: %s", str(e))
            return None

    def validate_token(self, access_token: str) -> GitHubTokenInfo | None:
        """
        Validate a GitHub OAuth access token and retrieve user information.

        Args:
            access_token: The GitHub OAuth access token from the frontend.

        Returns:
            GitHubTokenInfo with user details if valid, None if invalid.
        """
        try:
            with httpx.Client() as client:
                response = client.get(
                    self.GITHUB_USER_ENDPOINT,
                    headers={"Authorization": f"Bearer {access_token}"},
                    timeout=10.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    return GitHubTokenInfo(
                        id=data.get("id"),
                        login=data.get("login", ""),
                        email=data.get("email"),
                        name=data.get("name"),
                        avatar_url=data.get("avatar_url"),
                    )
                elif response.status_code == 401:
                    logger.debug("Invalid GitHub token")
                    return None
                else:
                    logger.error(
                        "Unexpected response from GitHub API: %s %s",
                        response.status_code,
                        response.text,
                    )
                    return None

        except httpx.RequestError as e:
            logger.error("Failed to validate GitHub token: %s", str(e))
            return None

    def get_user_email(self, access_token: str) -> str | None:
        """
        Get a verified primary email address from a GitHub user account.

        GitHub's /user endpoint may not always include the email, especially
        if the user hasn't made it public. This endpoint fetches the primary email.

        Args:
            access_token: The GitHub OAuth access token.

        Returns:
            Primary email address if found, None otherwise.
        """
        try:
            with httpx.Client() as client:
                response = client.get(
                    f"{self.GITHUB_API_BASE_URL}/user/emails",
                    headers={"Authorization": f"Bearer {access_token}"},
                    timeout=10.0,
                )

                if response.status_code == 200:
                    emails = response.json()
                    # Prefer a verified primary email, then any verified email.
                    verified_email: str | None = None
                    for email_obj in emails:
                        if email_obj.get("primary") and email_obj.get("verified"):
                            email: str | None = email_obj.get("email")
                            return email
                    for email_obj in emails:
                        if email_obj.get("verified"):
                            verified_email = email_obj.get("email")
                            if verified_email:
                                return verified_email
                    return None
                else:
                    logger.debug(
                        "Failed to get GitHub user emails: %s", response.status_code
                    )
                    return None
        except httpx.RequestError as e:
            logger.error("Failed to get GitHub user email: %s", str(e))
            return None
