"""WebSocket notifications endpoint backed by Redis pub/sub.

Connect via WebSocket:

    ws://HOST/api/v1/notifications/ws?token=<jwt>

Each connected client subscribes to their personal Redis channel
(``notifications:{user_id}``) and receives JSON-encoded
``NotificationOut`` messages in real time.

Superusers can push a notification to any user via:

    POST /api/v1/notifications/send

Any authenticated user can send a notification to themselves
(useful for testing the live connection) via:

    POST /api/v1/notifications/send/me
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
from typing import Annotated, Any, cast

import jwt
from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError
from sqlmodel import Session, select

from backend.api.deps import (
    CurrentUser,
    SessionDep,
    get_current_active_superuser,
    permission_dep,
)
from backend.core.auth import security
from backend.core.config import settings
from backend.core.db import get_engine
from backend.core.queue.redis import (
    get_redis_connection,
    notification_channel,
    publish_notification,
)
from backend.models import (
    Message,
    NotificationCreate,
    NotificationOut,
    NotificationSend,
    TokenPayload,
    User,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["notifications"])


def _consume_task_result(task: asyncio.Future[Any]) -> None:
    """Retrieve a finished task result and ignore expected disconnects."""
    with contextlib.suppress(asyncio.CancelledError, WebSocketDisconnect):
        task.result()


async def _cancel_task(task: asyncio.Task[Any]) -> None:
    """Cancel a pending task without leaking its cancellation during cleanup."""
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError, Exception):
        await task


def _get_user_from_token(token: str, session: Session) -> User | None:
    """Validate a JWT access token and return the active user, or ``None``."""
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (InvalidTokenError, ValidationError) as exc:
        logger.warning("WebSocket auth rejected — invalid token: %s", exc)
        return None
    if token_data.sub is None:
        logger.warning("WebSocket auth rejected — token has no 'sub' claim")
        return None
    try:
        user = cast(User | None, session.get(User, token_data.sub))
    except Exception:
        logger.exception(
            "WebSocket auth — database error looking up user %s", token_data.sub
        )
        return None
    if not user:
        logger.warning("WebSocket auth rejected — user %s not found", token_data.sub)
        return None
    if not user.is_active:
        logger.warning("WebSocket auth rejected — user %s is inactive", token_data.sub)
        return None
    return user


@router.websocket("/ws")
async def websocket_notifications(
    websocket: WebSocket,
    token: Annotated[str | None, Query(description="JWT access token")] = None,
) -> None:
    """Subscribe to real-time notifications over WebSocket.

    Authenticate by passing the JWT as a query parameter::

        ws://HOST/api/v1/notifications/ws?token=<jwt>

    The connection is closed with code **1008** (Policy Violation) when the
    token is missing or invalid.  Valid connections receive JSON-encoded
    ``NotificationOut`` objects whenever a message is published to the user's
    Redis channel.
    """
    # Create session manually - Depends() doesn't work reliably with WebSocket
    raw_token = token or websocket.cookies.get(security.SESSION_COOKIE_NAME)
    engine = get_engine()
    with Session(engine) as session:
        user = _get_user_from_token(raw_token or "", session)

    if user is None:
        await websocket.close(code=1008)
        return

    await websocket.accept()

    channel = notification_channel(str(user.id))
    redis_client = get_redis_connection()
    pubsub = redis_client.pubsub()

    try:
        await pubsub.subscribe(channel)
        logger.debug("User %s subscribed to channel %s", user.id, channel)

        async def _redis_to_ws() -> None:
            """Forward Redis pub/sub messages to the WebSocket."""
            async for message in pubsub.listen():
                if message["type"] == "message":
                    await websocket.send_text(message["data"])

        async def _ws_keepalive() -> None:
            """Drain incoming WebSocket frames; raises WebSocketDisconnect on close."""
            while True:
                await websocket.receive_text()

        redis_task = asyncio.create_task(_redis_to_ws())
        ws_task = asyncio.create_task(_ws_keepalive())

        _done, pending = await asyncio.wait(
            {redis_task, ws_task},
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in _done:
            _consume_task_result(task)
        for task in pending:
            await _cancel_task(task)

    except WebSocketDisconnect:
        pass

    finally:
        with contextlib.suppress(Exception):
            await pubsub.unsubscribe(channel)
        with contextlib.suppress(Exception):
            await pubsub.aclose()
        with contextlib.suppress(Exception):
            await redis_client.aclose()
        logger.debug("User %s disconnected from channel %s", user.id, channel)


@router.post(
    "/send",
    response_model=Message,
    dependencies=permission_dep("notifications:send_any"),
)
async def send_notification(
    *,
    notification_in: NotificationSend,
    _superuser: Annotated[User, Depends(get_current_active_superuser)],
) -> Message:
    """Send a notification to a specific user by ``user_id``.

    **Superusers only.**  The target user must be connected via WebSocket to
    receive the message in real time.
    """
    notification = NotificationOut(
        type=notification_in.type,
        title=notification_in.title,
        message=notification_in.message,
    )
    await publish_notification(
        str(notification_in.user_id),
        notification.model_dump_json(),
    )
    return Message(message="Notification sent")


@router.post("/send/me", response_model=Message)
async def send_notification_to_self(
    *,
    current_user: CurrentUser,
    notification_in: NotificationCreate,
) -> Message:
    """Send a notification to yourself.

    Useful for testing that your WebSocket connection is live without needing
    superuser privileges.
    """
    notification = NotificationOut(
        type=notification_in.type,
        title=notification_in.title,
        message=notification_in.message,
    )
    await publish_notification(
        str(current_user.id),
        notification.model_dump_json(),
    )
    return Message(message="Notification sent")


@router.post("/send/test-all", response_model=Message)
async def send_test_notification_to_all(
    *,
    session: SessionDep,
    _superuser: Annotated[User, Depends(get_current_active_superuser)],
) -> Message:
    """Send a test notification to all active users.

    **Superusers only.** Useful for testing WebSocket connections.
    """
    # Get all active users
    statement = select(User).where(User.is_active)
    users = session.exec(statement).all()

    if not users:
        return Message(message="No active users to notify")

    # Send test notification to each user
    notification = NotificationOut(
        type="info",
        title="Test Notification",
        message="WebSocket connection test - if you see this, your WebSocket is working!",
    )

    count = 0
    for user in users:
        try:
            await publish_notification(
                str(user.id),
                notification.model_dump_json(),
            )
            count += 1
        except Exception as exc:
            logger.warning(
                "Failed to send test notification to user %s: %s", user.id, exc
            )

    return Message(message=f"Test notification sent to {count} user(s)")
