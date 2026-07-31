"""Tests for GitHub OAuth authentication."""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from backend.core.config import settings
from backend.models import User


@pytest.mark.skipif(
    not settings.github_enabled,
    reason="GitHub OAuth not configured (GITHUB_CLIENT_ID not set)",
)
def test_github_login_with_verified_email(
    client: TestClient, db: Session, monkeypatch
) -> None:
    """GitHub login should use a verified email address for account linking."""
    from backend.core.auth.github import GitHubAuthClient, GitHubTokenInfo

    def mock_validate_token(self, access_token: str) -> GitHubTokenInfo | None:
        if access_token == "mock_token":
            return GitHubTokenInfo(
                id=123456,
                login="github-user",
                email="public-unverified@example.com",
                name="GitHub User",
            )
        return None

    def mock_get_user_email(self, access_token: str) -> str | None:
        if access_token == "mock_token":
            return "verified@example.com"
        return None

    monkeypatch.setattr(GitHubAuthClient, "validate_token", mock_validate_token)
    monkeypatch.setattr(GitHubAuthClient, "get_user_email", mock_get_user_email)

    response = client.post(
        "/api/v1/auth/github/login",
        json={"access_token": "mock_token"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    user = db.exec(select(User).where(User.email == "verified@example.com")).first()
    assert user is not None
    assert user.github_id == 123456
    assert user.github_username == "github-user"


@pytest.mark.skipif(
    not settings.github_enabled,
    reason="GitHub OAuth not configured (GITHUB_CLIENT_ID not set)",
)
def test_github_login_rejects_unverified_email(client: TestClient, monkeypatch) -> None:
    """GitHub login should fail when no verified email is available."""
    from backend.core.auth.github import GitHubAuthClient, GitHubTokenInfo

    def mock_validate_token(self, access_token: str) -> GitHubTokenInfo | None:
        if access_token == "mock_token":
            return GitHubTokenInfo(
                id=123456,
                login="github-user",
                email="public-unverified@example.com",
                name="GitHub User",
            )
        return None

    def mock_get_user_email(self, access_token: str) -> str | None:
        return None

    monkeypatch.setattr(GitHubAuthClient, "validate_token", mock_validate_token)
    monkeypatch.setattr(GitHubAuthClient, "get_user_email", mock_get_user_email)

    response = client.post(
        "/api/v1/auth/github/login",
        json={"access_token": "mock_token"},
    )

    assert response.status_code == 400
    assert "verified email" in response.json()["detail"]
