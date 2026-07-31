"""RQ job lifecycle callbacks — keep Task DB records in sync with RQ state.

These functions run inside the *worker* process, so they create their own
DB sessions rather than relying on FastAPI dependency injection.
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from typing import Any, cast

from redis import Redis
from rq.job import Job
from sqlmodel import Session, create_engine, select

from backend.core.config import settings
from backend.models import Task

logger = logging.getLogger(__name__)

_engine = None


def _get_engine() -> Any:
    global _engine
    if _engine is None:
        _engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))
    return _engine


def _get_task(session: Session, task_id: str) -> Task | None:
    try:
        return cast(Task | None, session.get(Task, uuid.UUID(task_id)))
    except Exception:
        statement = select(Task).where(Task.rq_job_id == task_id)
        return cast(Task | None, session.exec(statement).first())


def on_task_started(job: Job, _connection: Redis, *_args: Any, **_kwargs: Any) -> None:
    """Update task status when the worker starts executing a job."""
    task_id: str | None = (job.meta or {}).get("task_id")
    if not task_id:
        return
    try:
        with Session(_get_engine()) as session:
            db_task = _get_task(session, task_id)
            if db_task:
                db_task.status = "running"
                db_task.started_at = datetime.now(UTC)
                db_task.rq_job_id = job.id
                session.add(db_task)
                session.commit()
    except Exception:
        logger.exception("on_task_started failed for task_id=%s", task_id)


def on_task_success(
    job: Job, _connection: Redis, result: Any, *_args: Any, **_kwargs: Any
) -> None:
    """Update task status when a job finishes successfully."""
    task_id: str | None = (job.meta or {}).get("task_id")
    if not task_id:
        return
    try:
        with Session(_get_engine()) as session:
            db_task = _get_task(session, task_id)
            if db_task:
                db_task.status = "completed"
                db_task.result = (
                    result if isinstance(result, dict) else {"value": result}
                )
                db_task.completed_at = datetime.now(UTC)
                session.add(db_task)
                session.commit()
    except Exception:
        logger.exception("on_task_success failed for task_id=%s", task_id)


def on_task_failure(
    job: Job,
    _connection: Redis,
    type: type[BaseException],
    value: BaseException,
    _traceback: Any,
) -> None:
    """Update task status when a job raises an exception."""
    task_id: str | None = (job.meta or {}).get("task_id")
    if not task_id:
        return
    try:
        with Session(_get_engine()) as session:
            db_task = _get_task(session, task_id)
            if db_task:
                db_task.status = "failed"
                db_task.error = f"{type.__name__}: {value}"
                db_task.completed_at = datetime.now(UTC)
                session.add(db_task)
                session.commit()
    except Exception:
        logger.exception("on_task_failure failed for task_id=%s", task_id)


async def notify_user_task_progress(user_id: str, task_id: str, progress: int) -> None:
    """Notify a user of task progress via WebSocket."""
    import json

    from backend.core.queue.redis import publish_notification

    payload = json.dumps(
        {
            "type": "task_progress",
            "task_id": task_id,
            "progress": progress,
        }
    )
    await publish_notification(user_id, payload)
