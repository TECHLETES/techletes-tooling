from unittest.mock import patch

from fastapi.testclient import TestClient
from pwdlib.hashers.bcrypt import BcryptHasher
from sqlmodel import Session

from backend.core.config import settings
from backend.core.auth.security import get_password_hash, verify_password
from backend.crud import create_user
from backend.models import User, UserCreate
from backend.tests.utils.user import user_authentication_headers
from backend.tests.utils.utils import random_email, random_lower_string
from backend.utils.utils import generate_password_reset_token


def test_get_access_token(client: TestClient) -> None:
    login_data = {
        "username": settings.FIRST_SUPERUSER,
        "password": settings.FIRST_SUPERUSER_PASSWORD,
    }
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    tokens = r.json()
    assert r.status_code == 200
    assert "access_token" in tokens
    assert tokens["access_token"]
    set_cookie = r.headers.get("set-cookie", "")
    assert "access_token=" in set_cookie
    assert "session_present=1" in set_cookie


def test_use_cookie_session(client: TestClient) -> None:
    """A login cookie should authenticate normal API requests without a bearer header."""
    login_data = {
        "username": settings.FIRST_SUPERUSER,
        "password": settings.FIRST_SUPERUSER_PASSWORD,
    }
    login_response = client.post(
        f"{settings.API_V1_STR}/login/access-token", data=login_data
    )
    assert login_response.status_code == 200

    response = client.post(
        f"{settings.API_V1_STR}/login/test-token",
        cookies=login_response.cookies,
    )
    assert response.status_code == 200
    assert response.json()["email"] == settings.FIRST_SUPERUSER


def test_logout_clears_cookie_session(client: TestClient) -> None:
    """Logout should clear the auth cookie and JS-visible session marker."""
    login_data = {
        "username": settings.FIRST_SUPERUSER,
        "password": settings.FIRST_SUPERUSER_PASSWORD,
    }
    login_response = client.post(
        f"{settings.API_V1_STR}/login/access-token", data=login_data
    )
    assert login_response.status_code == 200

    logout_response = client.post(
        f"{settings.API_V1_STR}/login/logout",
        cookies=login_response.cookies,
    )
    assert logout_response.status_code == 200
    cleared_cookie = logout_response.headers.get_list("set-cookie")
    assert any(
        "access_token=" in header and "Max-Age=0" in header for header in cleared_cookie
    )
    assert any(
        "session_present=" in header and "Max-Age=0" in header
        for header in cleared_cookie
    )


def test_get_access_token_incorrect_password(client: TestClient) -> None:
    login_data = {
        "username": settings.FIRST_SUPERUSER,
        "password": "incorrect",
    }
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    assert r.status_code == 400


def test_use_access_token(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    r = client.post(
        f"{settings.API_V1_STR}/login/test-token",
        headers=superuser_token_headers,
    )
    result = r.json()
    assert r.status_code == 200
    assert "email" in result


def test_recovery_password(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    with (
        patch("backend.core.config.settings.SMTP_HOST", "smtp.example.com"),
        patch("backend.core.config.settings.SMTP_USER", "admin@example.com"),
    ):
        email = "test@example.com"
        r = client.post(
            f"{settings.API_V1_STR}/password-recovery/{email}",
            headers=normal_user_token_headers,
        )
        assert r.status_code == 200
        assert r.json() == {
            "message": "If that email is registered, we sent a password recovery link"
        }


def test_recovery_password_user_not_exits(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    email = "jVgQr@example.com"
    r = client.post(
        f"{settings.API_V1_STR}/password-recovery/{email}",
        headers=normal_user_token_headers,
    )
    # Should return 200 with generic message to prevent email enumeration attacks
    assert r.status_code == 200
    assert r.json() == {
        "message": "If that email is registered, we sent a password recovery link"
    }


def test_reset_password(client: TestClient, db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    new_password = random_lower_string()

    user_create = UserCreate(
        email=email,
        full_name="Test User",
        password=password,
        is_active=True,
        is_superuser=False,
    )
    user = create_user(session=db, user_create=user_create)
    token = generate_password_reset_token(email=email)
    headers = user_authentication_headers(client=client, email=email, password=password)
    data = {"new_password": new_password, "token": token}

    r = client.post(
        f"{settings.API_V1_STR}/reset-password/",
        headers=headers,
        json=data,
    )

    assert r.status_code == 200
    assert r.json() == {"message": "Password updated successfully"}

    db.refresh(user)
    verified, _ = verify_password(new_password, user.hashed_password)
    assert verified


def test_reset_password_invalid_token(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {"new_password": "changethis", "token": "invalid"}
    r = client.post(
        f"{settings.API_V1_STR}/reset-password/",
        headers=superuser_token_headers,
        json=data,
    )
    response = r.json()

    assert "detail" in response
    assert r.status_code == 400
    assert response["detail"] == "Invalid token"


def test_login_with_bcrypt_password_upgrades_to_argon2(
    client: TestClient, db: Session
) -> None:
    """Test that logging in with a bcrypt password hash upgrades it to argon2."""
    email = random_email()
    password = random_lower_string()

    # Create a bcrypt hash directly (simulating legacy password)
    bcrypt_hasher = BcryptHasher()
    bcrypt_hash = bcrypt_hasher.hash(password)
    assert bcrypt_hash.startswith("$2")  # bcrypt hashes start with $2

    user = User(email=email, hashed_password=bcrypt_hash, is_active=True)
    db.add(user)
    db.commit()
    db.refresh(user)

    assert user.hashed_password.startswith("$2")

    login_data = {"username": email, "password": password}
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    assert r.status_code == 200
    tokens = r.json()
    assert "access_token" in tokens

    db.refresh(user)

    # Verify the hash was upgraded to argon2
    assert user.hashed_password.startswith("$argon2")

    verified, updated_hash = verify_password(password, user.hashed_password)
    assert verified
    # Should not need another update since it's already argon2
    assert updated_hash is None


def test_login_with_argon2_password_keeps_hash(client: TestClient, db: Session) -> None:
    """Test that logging in with an argon2 password hash does not update it."""
    email = random_email()
    password = random_lower_string()

    # Create an argon2 hash (current default)
    argon2_hash = get_password_hash(password)
    assert argon2_hash.startswith("$argon2")

    # Create user with argon2 hash
    user = User(email=email, hashed_password=argon2_hash, is_active=True)
    db.add(user)
    db.commit()
    db.refresh(user)

    original_hash = user.hashed_password

    login_data = {"username": email, "password": password}
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    assert r.status_code == 200
    tokens = r.json()
    assert "access_token" in tokens

    db.refresh(user)

    assert user.hashed_password == original_hash
    assert user.hashed_password.startswith("$argon2")


def test_recover_password_nonexistent_email(client: TestClient) -> None:
    """Password recovery for non-existent email should still return success (for security)."""
    response = client.post(
        f"{settings.API_V1_STR}/password-recovery/nonexistent@example.com"
    )
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    # Should give generic message to prevent email enumeration
    assert "If that email is registered" in data["message"]


def test_reset_password_invalid_token_anonymous(client: TestClient) -> None:
    """Reset password with invalid token should fail (unauthenticated)."""
    response = client.post(
        f"{settings.API_V1_STR}/reset-password/",
        json={"token": "invalid-token-xyz", "new_password": "NewPassword123"},
    )
    assert response.status_code == 400
    assert "Invalid token" in response.json()["detail"]


def test_reset_password_empty_token(client: TestClient) -> None:
    """Reset password with empty token should fail."""
    response = client.post(
        f"{settings.API_V1_STR}/reset-password/",
        json={"token": "", "new_password": "NewPassword123"},
    )
    assert response.status_code in {400, 422}


def test_recover_password_html_requires_superuser(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
) -> None:
    """HTML password recovery endpoint requires superuser."""
    response = client.post(
        f"{settings.API_V1_STR}/password-recovery-html-content/test@example.com",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 403


def test_recover_password_html_nonexistent_user(
    client: TestClient,
    superuser_token_headers: dict[str, str],
) -> None:
    """HTML password recovery for non-existent user should return 404."""
    response = client.post(
        f"{settings.API_V1_STR}/password-recovery-html-content/nonexistent@example.com",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404


def test_recover_password_html_valid_user(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    """HTML password recovery for valid user should return HTML content."""
    from backend.tests.utils.user import create_random_user

    user = create_random_user(db)

    with patch("backend.api.routes.login.send_email"):
        response = client.post(
            f"{settings.API_V1_STR}/password-recovery-html-content/{user.email}",
            headers=superuser_token_headers,
        )

    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")


def test_reset_password_inactive_user(
    client: TestClient,
    db: Session,
) -> None:
    """Reset password for inactive user should fail."""
    from backend.tests.utils.user import create_random_user
    from backend.utils.utils import generate_password_reset_token

    user = create_random_user(db)
    user.is_active = False
    db.add(user)
    db.commit()

    token = generate_password_reset_token(email=user.email)

    response = client.post(
        f"{settings.API_V1_STR}/reset-password/",
        json={"token": token, "new_password": "NewPassword123"},
    )

    assert response.status_code == 400
    assert "Inactive user" in response.json()["detail"]
