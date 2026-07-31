from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from sqlmodel import Session

from backend.core.config import settings
from backend.models import Role, User


def test_get_entra_config_when_disabled(client: TestClient) -> None:
    """Test Entra config endpoint returns disabled state when not configured."""
    r = client.get(f"{settings.API_V1_STR}/auth/entra/config")
    assert r.status_code == 200
    data = r.json()
    assert "enabled" in data
    assert "client_id" in data


def test_entra_login_url_when_disabled(client: TestClient) -> None:
    """Test login URL endpoint returns error when Entra is not configured."""
    with patch.object(settings, "AZURE_CLIENT_ID", ""):
        r = client.get(
            f"{settings.API_V1_STR}/auth/entra/login-url",
            params={"redirect_uri": "http://localhost:3000/callback"},
        )
        assert r.status_code == 400


def test_entra_login_when_disabled(client: TestClient) -> None:
    """Test login endpoint returns error when Entra is not configured."""
    with patch.object(settings, "AZURE_CLIENT_ID", ""):
        r = client.post(
            f"{settings.API_V1_STR}/auth/entra/login",
            json={"id_token": "fake-token"},
        )
        assert r.status_code == 400


@patch("backend.api.routes.auth_entra.EntraAuthClient")
def test_entra_login_creates_user(
    mock_entra_client_class: MagicMock,
    client: TestClient,
    db: Session,
) -> None:
    """Test that Entra login creates a new user when one doesn't exist."""
    mock_client = MagicMock()
    mock_entra_client_class.return_value = mock_client
    mock_client.verify_id_token.return_value = {
        "oid": "azure-user-id-123",
        "preferred_username": "entra-test@example.com",
        "name": "Entra Test User",
        "tid": "test-tenant-id",
        "roles": ["Admin", "Editor"],
    }

    with (
        patch.object(settings, "AZURE_CLIENT_ID", "test-client-id"),
        patch.object(settings, "AZURE_CLIENT_SECRET", "test-secret"),
        patch.object(settings, "AZURE_TENANT_ID", "test-tenant-id"),
    ):
        r = client.post(
            f"{settings.API_V1_STR}/auth/entra/login",
            json={"id_token": "valid-id-token"},
        )
        assert r.status_code == 200
        data = r.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    # Verify user was created
    from sqlmodel import select

    user = db.exec(select(User).where(User.email == "entra-test@example.com")).first()
    assert user is not None
    assert user.azure_user_id == "azure-user-id-123"
    assert user.full_name == "Entra Test User"
    assert user.azure_roles == ["Admin", "Editor"]

    # Clean up
    db.delete(user)
    db.commit()


@patch("backend.api.routes.auth_entra.EntraAuthClient")
def test_entra_login_updates_existing_user(
    mock_entra_client_class: MagicMock,
    client: TestClient,
    db: Session,
) -> None:
    """Test that Entra login updates an existing user's Azure info."""
    # Create an existing user
    existing_user = User(
        email="entra-existing@example.com",
        full_name="Old Name",
        hashed_password="",
        is_active=True,
    )
    db.add(existing_user)
    db.commit()
    db.refresh(existing_user)

    mock_client = MagicMock()
    mock_entra_client_class.return_value = mock_client
    mock_client.verify_id_token.return_value = {
        "oid": "azure-user-id-456",
        "preferred_username": "entra-existing@example.com",
        "name": "Updated Name",
        "tid": "test-tenant-id",
        "roles": ["Viewer"],
    }

    with (
        patch.object(settings, "AZURE_CLIENT_ID", "test-client-id"),
        patch.object(settings, "AZURE_CLIENT_SECRET", "test-secret"),
        patch.object(settings, "AZURE_TENANT_ID", "test-tenant-id"),
    ):
        r = client.post(
            f"{settings.API_V1_STR}/auth/entra/login",
            json={"id_token": "valid-id-token"},
        )
        assert r.status_code == 200

    # Verify user was updated
    db.refresh(existing_user)
    assert existing_user.azure_user_id == "azure-user-id-456"
    assert existing_user.full_name == "Updated Name"
    assert existing_user.azure_roles == ["Viewer"]

    # Clean up
    db.delete(existing_user)
    db.commit()


@patch("backend.api.routes.auth_entra.EntraAuthClient")
def test_entra_login_maps_configured_superuser_role_to_super_admin(
    mock_entra_client_class: MagicMock,
    client: TestClient,
    db: Session,
) -> None:
    """Configured Entra superuser roles should resolve to the local Super admin role."""
    mock_client = MagicMock()
    mock_entra_client_class.return_value = mock_client
    mock_client.verify_id_token.return_value = {
        "oid": "azure-user-id-789",
        "preferred_username": "entra-super-admin@example.com",
        "name": "Entra Super admin",
        "tid": "test-tenant-id",
        "roles": ["Admin"],
    }

    with (
        patch.object(settings, "AZURE_CLIENT_ID", "test-client-id"),
        patch.object(settings, "AZURE_CLIENT_SECRET", "test-secret"),
        patch.object(settings, "AZURE_TENANT_ID", "test-tenant-id"),
        patch.object(settings, "AZURE_SUPERUSER_ROLE", "Admin"),
    ):
        r = client.post(
            f"{settings.API_V1_STR}/auth/entra/login",
            json={"id_token": "valid-id-token"},
        )
        assert r.status_code == 200
        access_token = r.json()["access_token"]

    from sqlmodel import select

    user = db.exec(
        select(User).where(User.email == "entra-super-admin@example.com")
    ).first()
    assert user is not None
    assert user.is_superuser is True

    super_admin_role = db.exec(select(Role).where(Role.name == "super_admin")).first()
    assert super_admin_role is not None
    assert any(role.id == super_admin_role.id for role in user.roles)
    assert all(role.name != "Admin" for role in user.roles)

    roles_response = client.get(
        f"{settings.API_V1_STR}/rbac/users/{user.id}/roles",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert roles_response.status_code == 200
    assert [role["name"] for role in roles_response.json()["data"]] == ["super_admin"]

    db.delete(user)
    db.commit()


@patch("backend.api.routes.auth_entra.EntraAuthClient")
def test_entra_login_ignores_client_supplied_roles(
    mock_entra_client_class: MagicMock,
    client: TestClient,
    db: Session,
) -> None:
    """Client-supplied roles must not grant privileges when verified token lacks them."""
    mock_client = MagicMock()
    mock_entra_client_class.return_value = mock_client
    mock_client.verify_id_token.return_value = {
        "oid": "azure-user-id-999",
        "preferred_username": "entra-no-roles@example.com",
        "name": "No Roles",
        "tid": "test-tenant-id",
        "roles": [],
    }

    with (
        patch.object(settings, "AZURE_CLIENT_ID", "test-client-id"),
        patch.object(settings, "AZURE_CLIENT_SECRET", "test-secret"),
        patch.object(settings, "AZURE_TENANT_ID", "test-tenant-id"),
        patch.object(settings, "AZURE_SUPERUSER_ROLE", "Admin"),
    ):
        r = client.post(
            f"{settings.API_V1_STR}/auth/entra/login",
            json={"id_token": "valid-id-token", "roles": ["Admin"]},
        )
        assert r.status_code == 200

    from sqlmodel import select

    user = db.exec(
        select(User).where(User.email == "entra-no-roles@example.com")
    ).first()
    assert user is not None
    assert user.is_superuser is False
    assert user.azure_roles == []

    db.delete(user)
    db.commit()


@patch("backend.api.routes.auth_entra.EntraAuthClient")
def test_entra_login_invalid_token(
    mock_entra_client_class: MagicMock,
    client: TestClient,
) -> None:
    """Test that Entra login fails with invalid token."""
    mock_client = MagicMock()
    mock_entra_client_class.return_value = mock_client
    mock_client.verify_id_token.side_effect = Exception("Invalid token")

    with (
        patch.object(settings, "AZURE_CLIENT_ID", "test-client-id"),
        patch.object(settings, "AZURE_CLIENT_SECRET", "test-secret"),
    ):
        r = client.post(
            f"{settings.API_V1_STR}/auth/entra/login",
            json={"id_token": "invalid-token"},
        )
        assert r.status_code == 400


@patch("backend.api.routes.auth_entra.EntraAuthClient")
def test_entra_login_logs_token_validation_failure(
    mock_entra_client_class: MagicMock,
    client: TestClient,
    caplog,
) -> None:
    """Entra login should log the verification failure reason."""
    mock_client = MagicMock()
    mock_entra_client_class.return_value = mock_client
    mock_client.verify_id_token.side_effect = Exception("issuer mismatch")

    with (
        patch.object(settings, "AZURE_CLIENT_ID", "test-client-id"),
        patch.object(settings, "AZURE_CLIENT_SECRET", "test-secret"),
        patch.object(settings, "AZURE_TENANT_ID", "test-tenant-id"),
        caplog.at_level("ERROR"),
    ):
        r = client.post(
            f"{settings.API_V1_STR}/auth/entra/login",
            json={"id_token": "invalid-token"},
        )

    assert r.status_code == 400
    assert "issuer mismatch" in r.json()["detail"]
    assert "Microsoft Entra login failed during ID token verification" in caplog.text


def test_tenant_crud_requires_superuser(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
) -> None:
    """Test that tenant management endpoints require superuser."""
    r = client.get(
        f"{settings.API_V1_STR}/tenants/",
        headers=normal_user_token_headers,
    )
    assert r.status_code == 403


def test_tenant_crud_list(
    client: TestClient,
    superuser_token_headers: dict[str, str],
) -> None:
    """Test listing tenants as superuser."""
    r = client.get(
        f"{settings.API_V1_STR}/tenants/",
        headers=superuser_token_headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert "data" in data
    assert "count" in data


def test_tenant_crud_create_and_delete(
    client: TestClient,
    superuser_token_headers: dict[str, str],
) -> None:
    """Test creating and deleting a tenant."""
    # Create
    r = client.post(
        f"{settings.API_V1_STR}/tenants/",
        headers=superuser_token_headers,
        json={
            "tenant_id": "test-tenant-create-delete",
            "tenant_name": "Test Tenant",
            "is_enabled": True,
            "auto_create_users": True,
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["tenant_id"] == "test-tenant-create-delete"
    assert data["tenant_name"] == "Test Tenant"

    # Duplicate
    r = client.post(
        f"{settings.API_V1_STR}/tenants/",
        headers=superuser_token_headers,
        json={
            "tenant_id": "test-tenant-create-delete",
            "tenant_name": "Duplicate Tenant",
        },
    )
    assert r.status_code == 400

    # Delete
    r = client.delete(
        f"{settings.API_V1_STR}/tenants/test-tenant-create-delete",
        headers=superuser_token_headers,
    )
    assert r.status_code == 200


def test_tenant_crud_update(
    client: TestClient,
    superuser_token_headers: dict[str, str],
) -> None:
    """Test updating a tenant."""
    # Create first
    r = client.post(
        f"{settings.API_V1_STR}/tenants/",
        headers=superuser_token_headers,
        json={
            "tenant_id": "test-tenant-update",
            "tenant_name": "Original Name",
        },
    )
    assert r.status_code == 200

    # Update
    r = client.patch(
        f"{settings.API_V1_STR}/tenants/test-tenant-update",
        headers=superuser_token_headers,
        json={"tenant_name": "Updated Name", "is_enabled": False},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["tenant_name"] == "Updated Name"
    assert data["is_enabled"] is False

    # Clean up
    client.delete(
        f"{settings.API_V1_STR}/tenants/test-tenant-update",
        headers=superuser_token_headers,
    )


def test_tenant_delete_not_found(
    client: TestClient,
    superuser_token_headers: dict[str, str],
) -> None:
    """Test deleting a non-existent tenant returns 404."""
    r = client.delete(
        f"{settings.API_V1_STR}/tenants/non-existent-tenant",
        headers=superuser_token_headers,
    )
    assert r.status_code == 404


@patch("backend.api.routes.auth_entra.EntraAuthClient")
def test_entra_login_url_when_enabled(
    mock_entra_client_class: MagicMock,
    client: TestClient,
) -> None:
    """Test login URL is returned when Entra is configured."""
    mock_client = MagicMock()
    mock_entra_client_class.return_value = mock_client
    mock_client.get_login_url.return_value = "https://login.microsoftonline.com/test"

    with (
        patch.object(settings, "AZURE_CLIENT_ID", "test-client-id"),
        patch.object(settings, "AZURE_CLIENT_SECRET", "test-secret"),
    ):
        r = client.get(
            f"{settings.API_V1_STR}/auth/entra/login-url",
            params={"redirect_uri": "http://localhost:3000/callback"},
        )
        assert r.status_code == 200
        data = r.json()
        assert "login_url" in data
