"""Google OAuth authentication client utilities."""

import logging

import httpx
from pydantic import BaseModel

from backend.core.config import settings

logger = logging.getLogger(__name__)


class GoogleTokenInfo(BaseModel):
    """User information from Google OAuth token."""

    sub: str  # Google user ID
    email: str
    email_verified: bool
    name: str | None = None
    picture: str | None = None
    given_name: str | None = None
    family_name: str | None = None


class GoogleAuthClient:
    """Handle Google OAuth authentication."""

    GOOGLE_TOKEN_INFO_URL = "https://www.googleapis.com/oauth2/v3/tokeninfo"
    GOOGLE_USER_INFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

    def __init__(self) -> None:
        """Initialize the Google auth client with configuration values."""
        self.client_id = settings.GOOGLE_CLIENT_ID
        self.client_secret = settings.GOOGLE_CLIENT_SECRET

    def validate_token(self, access_token: str) -> GoogleTokenInfo | None:
        """
        Validate a Google OAuth access token and retrieve user information.

        Attempts to fetch user info from the Google tokeninfo endpoint.

        Args:
            access_token: The Google OAuth access token from the frontend.

        Returns:
            GoogleTokenInfo with user details if valid, None if invalid.

        Raises:
            Exception: If the HTTP request fails unexpectedly.
        """
        try:
            with httpx.Client() as client:
                # Try tokeninfo endpoint first (faster, doesn't require client secret)
                response = client.get(
                    self.GOOGLE_TOKEN_INFO_URL,
                    params={"access_token": access_token},
                    timeout=10.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    # Validate that the token is for our app
                    if data.get("aud") != self.client_id:
                        logger.warning(
                            "Google token audience mismatch: %s != %s",
                            data.get("aud"),
                            self.client_id,
                        )
                        return None

                    return GoogleTokenInfo(
                        sub=data.get("sub", ""),
                        email=data.get("email", ""),
                        email_verified=data.get("email_verified", False),
                        name=data.get("name"),
                        picture=data.get("picture"),
                        given_name=data.get("given_name"),
                        family_name=data.get("family_name"),
                    )

                elif response.status_code == 400:
                    logger.debug(
                        "Invalid Google token: %s", response.json().get("error")
                    )
                    return None

                else:
                    logger.error(
                        "Unexpected response from Google tokeninfo: %s %s",
                        response.status_code,
                        response.text,
                    )
                    return None

        except httpx.RequestError as e:
            logger.error("Failed to validate Google token: %s", str(e))
            raise Exception(f"Failed to validate Google token: {str(e)}") from e

    def exchange_code_for_token(self, code: str) -> str | None:
        """Exchange an OAuth authorization code for an access token."""
        try:
            with httpx.Client() as client:
                response = client.post(
                    "https://oauth2.googleapis.com/token",
                    data={
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "code": code,
                        "grant_type": "authorization_code",
                    },
                    timeout=10.0,
                )

                if response.status_code == 200:
                    token = response.json().get("access_token")
                    return token if isinstance(token, str) else None

                logger.error(
                    "Failed to exchange Google code for token: %s %s",
                    response.status_code,
                    response.text,
                )
                return None
        except httpx.RequestError as e:
            logger.error("Failed to exchange Google code for token: %s", str(e))
            return None

    def get_user_info(self, access_token: str) -> GoogleTokenInfo | None:
        """
        Get detailed user information from Google using an access token.

        This is an alternative to validate_token() with more detailed info.

        Args:
            access_token: The Google OAuth access token from the frontend.

        Returns:
            GoogleTokenInfo with user details if valid, None if invalid.
        """
        try:
            with httpx.Client() as client:
                response = client.get(
                    self.GOOGLE_USER_INFO_URL,
                    headers={"Authorization": f"Bearer {access_token}"},
                    timeout=10.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    return GoogleTokenInfo(
                        sub=data.get("id", ""),
                        email=data.get("email", ""),
                        email_verified=data.get("verified_email", False),
                        name=data.get("name"),
                        picture=data.get("picture"),
                        given_name=data.get("given_name"),
                        family_name=data.get("family_name"),
                    )
                else:
                    logger.debug(
                        "Failed to get Google user info: %s", response.status_code
                    )
                    return None

        except httpx.RequestError as e:
            logger.error("Failed to get Google user info: %s", str(e))
            return None
