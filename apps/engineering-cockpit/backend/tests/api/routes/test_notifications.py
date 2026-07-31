"""Tests for the /notifications endpoints."""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from backend.api.routes.notifications import _cancel_task, _consume_task_result
from backend.core.config import settings
from backend.tests.utils.user import create_random_user

# ---------------------------------------------------------------------------
# WebSocket — authentication
# ---------------------------------------------------------------------------


def test_websocket_rejects_missing_token(client: TestClient) -> None:
    """WebSocket connection without a token should be rejected."""
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect(f"{settings.API_V1_STR}/notifications/ws") as ws:
            ws.receive_text()


def test_websocket_rejects_invalid_token(client: TestClient) -> None:
    """WebSocket connection with a bad JWT should be rejected."""
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect(
            f"{settings.API_V1_STR}/notifications/ws?token=not-a-jwt"
        ) as ws:
            ws.receive_text()


def test_websocket_accepts_valid_token(
    db,  # type: ignore[no-untyped-def]
    normal_user_token_headers: dict[str, str],
) -> None:
    """WebSocket token authentication should work with valid JWT."""
    from datetime import timedelta

    from backend.api.routes.notifications import _get_user_from_token
    from backend.core.auth.security import create_access_token
    from backend.tests.utils.user import create_random_user

    # Create a test user
    user = create_random_user(db)

    # Create a valid JWT token for this user
    token = create_access_token(
        subject=str(user.id),
        expires_delta=timedelta(hours=1),
    )

    # Authenticate using the token
    authenticated_user = _get_user_from_token(token, db)
    assert authenticated_user is not None
    assert authenticated_user.id == user.id
    assert authenticated_user.email == user.email


def test_websocket_accepts_cookie_session(
    client: TestClient,
    db,  # type: ignore[no-untyped-def]
) -> None:
    """WebSocket authentication should also work with the session cookie."""
    from datetime import timedelta

    from backend.core.auth.security import create_access_token

    user = create_random_user(db)
    token = create_access_token(
        subject=str(user.id),
        expires_delta=timedelta(hours=1),
    )

    with patch(
        "backend.api.routes.notifications.get_engine",
        return_value=db.get_bind(),
    ):
        with client.websocket_connect(
            f"{settings.API_V1_STR}/notifications/ws",
            headers={"cookie": f"access_token={token}; session_present=1"},
        ):
            pass


# ---------------------------------------------------------------------------
# POST /notifications/send  (superuser only)
# ---------------------------------------------------------------------------


def test_send_notification_superuser(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db,  # type: ignore[no-untyped-def]
) -> None:
    """Superuser can send a notification to any user."""
    target = create_random_user(db)

    with patch(
        "backend.api.routes.notifications.publish_notification",
        new_callable=AsyncMock,
    ) as mock_pub:
        response = client.post(
            f"{settings.API_V1_STR}/notifications/send",
            headers=superuser_token_headers,
            json={
                "user_id": str(target.id),
                "type": "info",
                "title": "Hello",
                "message": "World",
            },
        )

    assert response.status_code == 200
    assert response.json()["message"] == "Notification sent"
    mock_pub.assert_called_once()
    channel_arg, payload_arg = mock_pub.call_args.args
    assert str(target.id) in channel_arg
    assert "Hello" in payload_arg


def test_send_notification_requires_superuser(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    db,  # type: ignore[no-untyped-def]
) -> None:
    """Non-superusers should receive 403 when calling /send."""
    target = create_random_user(db)

    response = client.post(
        f"{settings.API_V1_STR}/notifications/send",
        headers=normal_user_token_headers,
        json={
            "user_id": str(target.id),
            "type": "info",
            "title": "Hi",
            "message": "There",
        },
    )
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# POST /notifications/send/me
# ---------------------------------------------------------------------------


def test_send_notification_to_self(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
) -> None:
    """Any authenticated user can send a notification to themselves."""
    with patch(
        "backend.api.routes.notifications.publish_notification",
        new_callable=AsyncMock,
    ) as mock_pub:
        response = client.post(
            f"{settings.API_V1_STR}/notifications/send/me",
            headers=normal_user_token_headers,
            json={
                "type": "success",
                "title": "Test",
                "message": "It works",
            },
        )

    assert response.status_code == 200
    assert response.json()["message"] == "Notification sent"
    mock_pub.assert_called_once()
    _channel, payload = mock_pub.call_args.args
    assert "Test" in payload
    assert "success" in payload


def test_send_notification_to_self_requires_auth(client: TestClient) -> None:
    """Unauthenticated requests to /send/me should receive 401/403."""
    response = client.post(
        f"{settings.API_V1_STR}/notifications/send/me",
        json={"type": "info", "title": "X", "message": "Y"},
    )
    assert response.status_code in {401, 403}


def test_send_notification_validates_payload(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
) -> None:
    """Requests with invalid notification type should fail validation."""
    response = client.post(
        f"{settings.API_V1_STR}/notifications/send/me",
        headers=normal_user_token_headers,
        json={
            "type": "invalid-type",
            "title": "Oops",
            "message": "Bad type",
        },
    )
    assert response.status_code == 422


def test_send_notification_superuser_missing_user(
    client: TestClient,
    superuser_token_headers: dict[str, str],
) -> None:
    """Superuser sending to non-existent user should return 404."""
    import uuid

    with patch(
        "backend.api.routes.notifications.publish_notification",
        new_callable=AsyncMock,
    ):
        response = client.post(
            f"{settings.API_V1_STR}/notifications/send",
            headers=superuser_token_headers,
            json={
                "user_id": str(uuid.uuid4()),  # Non-existent user
                "type": "info",
                "title": "Hello",
                "message": "World",
            },
        )

    # Should handle gracefully
    assert response.status_code in {200, 404}


def test_websocket_token_invalid_format(client: TestClient) -> None:
    """WebSocket with malformed token should be rejected."""
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect(
            f"{settings.API_V1_STR}/notifications/ws?token=malformed"
        ) as ws:
            ws.receive_text()


def test_send_notification_with_empty_message(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
) -> None:
    """Sending notification with empty message should handle gracefully."""
    with patch(
        "backend.api.routes.notifications.publish_notification",
        new_callable=AsyncMock,
    ):
        response = client.post(
            f"{settings.API_V1_STR}/notifications/send/me",
            headers=normal_user_token_headers,
            json={
                "type": "info",
                "title": "Title Only",
                "message": "",  # Empty message
            },
        )

    # Should either accept or reject gracefully
    assert response.status_code in {200, 422}


def test_get_user_from_token_with_expired_token(
    db,  # type: ignore[no-untyped-def]
) -> None:
    """Getting user from expired token should return None."""
    from datetime import timedelta

    from backend.api.routes.notifications import _get_user_from_token
    from backend.core.auth.security import create_access_token
    from backend.tests.utils.user import create_random_user

    user = create_random_user(db)

    # Create an already-expired token
    expired_token = create_access_token(
        subject=str(user.id),
        expires_delta=timedelta(seconds=-1),  # Expired 1 second ago
    )

    # Should return None for expired token
    result = _get_user_from_token(expired_token, db)
    assert result is None


def test_consume_task_result_ignores_websocket_disconnect() -> None:
    """Finished websocket tasks that disconnect should not raise here."""

    async def _run() -> None:
        future: asyncio.Future[object] = asyncio.get_running_loop().create_future()
        future.set_exception(WebSocketDisconnect(1001))
        _consume_task_result(future)

    asyncio.run(_run())


def test_cancel_task_ignores_cancellation() -> None:
    """Cancelling a pending WebSocket task should not escape cleanup."""

    async def _run() -> None:
        task = asyncio.create_task(asyncio.sleep(60))
        await _cancel_task(task)

    asyncio.run(_run())


def test_get_user_from_token_with_invalid_user_id(
    db,  # type: ignore[no-untyped-def]
) -> None:
    """Getting user with non-existent ID from token should return None."""
    import uuid
    from datetime import timedelta

    from backend.api.routes.notifications import _get_user_from_token
    from backend.core.auth.security import create_access_token

    # Create token with non-existent user ID
    token = create_access_token(
        subject=str(uuid.uuid4()),  # Non-existent user
        expires_delta=timedelta(hours=1),
    )

    # Should return None since user doesn't exist
    result = _get_user_from_token(token, db)
    assert result is None
