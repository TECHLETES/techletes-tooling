"""Tests for utils routes."""

from fastapi.testclient import TestClient


def test_health_check(client: TestClient) -> None:
    """Test health check endpoint."""
    response = client.get("/api/v1/utils/health-check/")
    assert response.status_code == 200
    assert response.json() is True


def test_get_app_config(client: TestClient) -> None:
    """Test getting application config."""
    response = client.get("/api/v1/utils/config")
    assert response.status_code == 200
    data = response.json()
    assert "signup_enabled" in data
    assert isinstance(data["signup_enabled"], bool)


def test_test_email_requires_superuser(
    client: TestClient, normal_user_token_headers: dict
) -> None:
    """Test that test email endpoint requires superuser."""
    response = client.post(
        "/api/v1/utils/test-email/",
        headers=normal_user_token_headers,
        params={"email_to": "test@example.com"},
    )
    assert response.status_code == 403
