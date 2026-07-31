"""Tests for GitHub auth helpers."""

from unittest.mock import MagicMock

from backend.core.auth.github import GitHubAuthClient


def test_get_user_email_prefers_verified_primary(monkeypatch) -> None:
    """Prefer a verified primary email over other addresses."""
    client = GitHubAuthClient()

    response = MagicMock()
    response.status_code = 200
    response.json.return_value = [
        {"email": "unverified-primary@example.com", "primary": True, "verified": False},
        {"email": "verified-secondary@example.com", "primary": False, "verified": True},
        {"email": "verified-primary@example.com", "primary": True, "verified": True},
    ]

    httpx_client = MagicMock()
    httpx_client.__enter__.return_value = httpx_client
    httpx_client.__exit__.return_value = None
    httpx_client.get.return_value = response
    monkeypatch.setattr("backend.core.auth.github.httpx.Client", lambda: httpx_client)

    assert client.get_user_email("token") == "verified-primary@example.com"


def test_get_user_email_rejects_unverified_fallback(monkeypatch) -> None:
    """Return no email when GitHub has no verified addresses."""
    client = GitHubAuthClient()

    response = MagicMock()
    response.status_code = 200
    response.json.return_value = [
        {"email": "primary@example.com", "primary": True, "verified": False},
        {"email": "secondary@example.com", "primary": False, "verified": False},
    ]

    httpx_client = MagicMock()
    httpx_client.__enter__.return_value = httpx_client
    httpx_client.__exit__.return_value = None
    httpx_client.get.return_value = response
    monkeypatch.setattr("backend.core.auth.github.httpx.Client", lambda: httpx_client)

    assert client.get_user_email("token") is None
