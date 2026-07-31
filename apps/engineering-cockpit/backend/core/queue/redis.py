"""Redis connection manager and pub/sub utilities for real-time notifications."""

from __future__ import annotations

import contextlib
import logging

import redis.asyncio as aioredis

from backend.core.config import settings

logger = logging.getLogger(__name__)

_pool: aioredis.ConnectionPool | None = None


def _get_pool() -> aioredis.ConnectionPool:
    """Return (or lazily create) the shared async connection pool."""
    global _pool
    if _pool is None:
        _pool = aioredis.ConnectionPool.from_url(
            settings.REDIS_URL,
            max_connections=20,
            decode_responses=True,
        )
    return _pool


def get_redis_connection() -> aioredis.Redis:
    """Return an async Redis client backed by the shared connection pool."""
    return aioredis.Redis(connection_pool=_get_pool())


def notification_channel(user_id: str) -> str:
    """Return the Redis pub/sub channel name for a user's notifications."""
    return f"notifications:{user_id}"


async def publish_notification(user_id: str, payload: str) -> None:
    """Publish a JSON notification payload to a user's Redis channel."""
    client = get_redis_connection()
    try:
        await client.publish(notification_channel(user_id), payload)
    finally:
        with contextlib.suppress(Exception):
            await client.aclose()
