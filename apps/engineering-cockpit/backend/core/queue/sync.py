"""RQ queue setup – synchronous Redis connection for background job processing."""

from __future__ import annotations

from typing import Literal

import redis
from rq import Queue

from backend.core.config import settings

# Synchronous Redis connection for RQ (not the async client used for pub/sub)
_redis_conn: redis.Redis | None = None


def get_redis_conn() -> redis.Redis:
    """Return a lazily-created synchronous Redis connection."""
    global _redis_conn
    if _redis_conn is None:
        _redis_conn = redis.Redis.from_url(settings.REDIS_URL, decode_responses=False)
    return _redis_conn


def get_queue(
    name: Literal["default", "high", "low"] = "default",
) -> Queue:
    """Return an RQ Queue for the given priority level."""
    return Queue(name, connection=get_redis_conn())
