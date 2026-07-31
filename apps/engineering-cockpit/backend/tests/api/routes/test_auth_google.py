"""Tests for Google OAuth authentication."""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from backend.core.config import settings
from backend.models import User


@pytest.mark.skipif(
    not settings.google_enabled,
    reason="Google OAuth not configured (GOOGLE_CLIENT_ID not set)",
)
def test_google_config_endpoint(client: TestClient) -> None:
    """Test that Google config endpoint returns configuration."""
    response = client.get("/api/v1/auth/google/config")
    assert response.status_code == 200

    data = response.json()
    assert "enabled" in data
    assert "client_id" in data
    assert data["enabled"] is True
    assert data["client_id"] == settings.GOOGLE_CLIENT_ID


def test_google_config_disabled(client: TestClient) -> None:
    """Test that Google config returns disabled when not configured."""
    # This test will pass as long as we can call the endpoint
    response = client.get("/api/v1/auth/google/config")
    assert response.status_code == 200

    data = response.json()
    assert "enabled" in data
    # If not configured, enabled will be False
    if not settings.google_enabled:
        assert data["enabled"] is False
        assert data["client_id"] is None


@pytest.mark.skipif(
    not settings.google_enabled,
    reason="Google OAuth not configured (GOOGLE_CLIENT_ID not set)",
)
def test_google_login_invalid_token(client: TestClient, db: Session) -> None:
    """Test that invalid Google token returns 400."""
    response = client.post(
        "/api/v1/auth/google/login",
        json={"access_token": "invalid_token_12345"},
    )
    assert response.status_code == 400
    assert (
        "Failed to validate Google token" in response.json()["detail"]
        or "Invalid or expired Google token" in response.json()["detail"]
    )


@pytest.mark.skipif(
    not settings.google_enabled,
    reason="Google OAuth not configured (GOOGLE_CLIENT_ID not set)",
)
def test_google_login_with_mock_token(
    client: TestClient, db: Session, monkeypatch
) -> None:
    """Test Google login with a mocked token validation."""
    from backend.core.auth.google import GoogleAuthClient, GoogleTokenInfo

    # Mock the Google token validation
    def mock_validate_token(self, access_token: str) -> GoogleTokenInfo | None:
        if access_token == "mock_token":
            return GoogleTokenInfo(
                sub="123456789",
                email="testuser@gmail.com",
                email_verified=True,
                name="Test User",
                picture="https://example.com/photo.jpg",
            )
        return None

    monkeypatch.setattr(GoogleAuthClient, "validate_token", mock_validate_token)

    # Attempt login with mock token
    response = client.post(
        "/api/v1/auth/google/login",
        json={"access_token": "mock_token"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    # Verify user was created
    user = db.exec(select(User).where(User.email == "testuser@gmail.com")).first()
    assert user is not None
    assert user.google_id == "123456789"
    assert user.google_email == "testuser@gmail.com"
    assert user.full_name == "Test User"
    assert user.is_active is True
    assert user.is_superuser is False


@pytest.mark.skipif(
    not settings.google_enabled,
    reason="Google OAuth not configured (GOOGLE_CLIENT_ID not set)",
)
def test_google_login_account_linking(
    client: TestClient, db: Session, monkeypatch
) -> None:
    """Test that Google login can link to an existing email-based account."""
    from backend.core.auth.google import GoogleAuthClient, GoogleTokenInfo
    from backend.core.auth import security

    # Create an existing user with email/password auth
    existing_user = User(
        email="existing@example.com",
        hashed_password=security.get_password_hash("password123"),
        full_name="Existing User",
        is_active=True,
        is_superuser=False,
    )
    db.add(existing_user)
    db.commit()

    # Mock Google validation for the same email
    def mock_validate_token(self, access_token: str) -> GoogleTokenInfo | None:
        if access_token == "mock_token":
            return GoogleTokenInfo(
                sub="google_id_123",
                email="existing@example.com",
                email_verified=True,
                name="Existing User",
            )
        return None

    monkeypatch.setattr(GoogleAuthClient, "validate_token", mock_validate_token)

    # Login with Google using the same email
    response = client.post(
        "/api/v1/auth/google/login",
        json={"access_token": "mock_token"},
    )

    assert response.status_code == 200

    # Verify the existing user now has Google ID linked
    user = db.exec(select(User).where(User.email == "existing@example.com")).first()
    assert user is not None
    assert user.google_id == "google_id_123"
    assert user.google_email == "existing@example.com"


@pytest.mark.skipif(
    not settings.google_enabled,
    reason="Google OAuth not configured (GOOGLE_CLIENT_ID not set)",
)
def test_google_login_unverified_email(client: TestClient, monkeypatch) -> None:
    """Test that unverified email returns 400."""
    from backend.core.auth.google import GoogleAuthClient, GoogleTokenInfo

    def mock_validate_token(self, access_token: str) -> GoogleTokenInfo | None:
        if access_token == "unverified_token":
            return GoogleTokenInfo(
                sub="123456789",
                email="unverified@example.com",
                email_verified=False,  # Email not verified
                name="Test User",
            )
        return None

    monkeypatch.setattr(GoogleAuthClient, "validate_token", mock_validate_token)

    response = client.post(
        "/api/v1/auth/google/login",
        json={"access_token": "unverified_token"},
    )

    assert response.status_code == 400
    assert "email is not verified" in response.json()["detail"]


@pytest.mark.skipif(
    not settings.google_enabled,
    reason="Google OAuth not configured (GOOGLE_CLIENT_ID not set)",
)
def test_google_exchange_code_with_mock_token(client: TestClient, monkeypatch) -> None:
    """Test Google auth-code login with a mocked code exchange."""
    from backend.core.auth.google import GoogleAuthClient, GoogleTokenInfo

    def mock_exchange_code_for_token(self, code: str) -> str | None:
        if code == "mock_code":
            return "mock_access_token"
        return None

    def mock_validate_token(self, access_token: str) -> GoogleTokenInfo | None:
        if access_token == "mock_access_token":
            return GoogleTokenInfo(
                sub="123456789",
                email="codeuser@gmail.com",
                email_verified=True,
                name="Code User",
                picture="https://example.com/photo.jpg",
            )
        return None

    monkeypatch.setattr(
        GoogleAuthClient, "exchange_code_for_token", mock_exchange_code_for_token
    )
    monkeypatch.setattr(GoogleAuthClient, "validate_token", mock_validate_token)

    response = client.post(
        "/api/v1/auth/google/exchange-code",
        json={"code": "mock_code"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
