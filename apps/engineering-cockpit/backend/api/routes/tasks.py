"""Background task enqueueing and status endpoints."""

import importlib
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, status
from rq import Callback
from rq.exceptions import NoSuchJobError
from rq.job import Job

from backend import crud
from backend.api.deps import CurrentUser, SessionDep, permission_dep
from backend.core.queue import get_queue, get_redis_conn
from backend.core.queue.callbacks import (
    on_task_failure,
    on_task_started,
    on_task_success,
)
from backend.models import TaskCreate, TaskPublic, TasksPublic

router = APIRouter(prefix="/tasks", tags=["tasks"])

# ---------------------------------------------------------------------------
# Task registry
# ---------------------------------------------------------------------------

TASK_MAP: dict[str, str] = {
    "send_email": "backend.tasks.example.send_email_task",
    "export_data": "backend.tasks.example.export_data_task",
    "process_file": "backend.tasks.example.process_file_task",
}


def _load_task_func(task_type: str) -> Any:
    func_path = TASK_MAP[task_type]
    module_path, func_name = func_path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    return getattr(module, func_name)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/enqueue",
    response_model=TaskPublic,
)
def enqueue_task(
    *,
    body: TaskCreate,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """Create a DB task record and enqueue it for background processing."""
    db_task = crud.create_task(session=session, task_in=body, owner_id=current_user.id)

    func = _load_task_func(body.task_type)
    q = get_queue(body.queue)

    # Pass task_id via meta and as kwarg so the function and callbacks can update DB
    kwargs = dict(body.kwargs)
    kwargs["_task_id"] = str(db_task.id)

    job = q.enqueue(
        func,
        kwargs=kwargs,
        meta={"task_id": str(db_task.id)},
        on_started=Callback(on_task_started),
        on_success=Callback(on_task_success),
        on_failure=Callback(on_task_failure),
    )

    # Store the RQ job ID in the DB record
    db_task = crud.update_task_status(
        session=session,
        db_task=db_task,
        status="queued",
        rq_job_id=job.id,
    )
    return db_task


@router.get(
    "/",
    response_model=TasksPublic,
)
def list_tasks(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    status: str | None = None,
    task_type: str | None = None,
    queue: str | None = None,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """List the current user's tasks."""
    return crud.list_tasks(
        session=session,
        owner_id=current_user.id,
        status=status,
        task_type=task_type,
        queue=queue,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{task_id}",
    response_model=TaskPublic,
)
def get_task(
    task_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """Get a task by its database ID."""
    db_task = crud.get_task(session=session, task_id=task_id)
    if not db_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )
    if db_task.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )
    return db_task


@router.delete(
    "/{task_id}",
    response_model=TaskPublic,
    dependencies=permission_dep("tasks:delete"),
)
def cancel_task(
    task_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """Cancel a queued or running task."""
    db_task = crud.get_task(session=session, task_id=task_id)
    if not db_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )
    if db_task.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )

    if db_task.status not in ("queued", "running"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot cancel task with status '{db_task.status}'",
        )

    # Attempt to cancel the RQ job (best-effort)
    if db_task.rq_job_id:
        try:
            job = Job.fetch(db_task.rq_job_id, connection=get_redis_conn())
            job.cancel()
        except (NoSuchJobError, Exception):
            pass  # Job may have already finished; still update DB

    db_task = crud.update_task_status(
        session=session,
        db_task=db_task,
        status="cancelled",
    )
    return db_task


# ---------------------------------------------------------------------------
# Superuser: list all tasks across all users
# ---------------------------------------------------------------------------


@router.get(
    "/admin/all",
    response_model=TasksPublic,
    dependencies=permission_dep("admin:manage_tasks"),
)
def list_all_tasks(
    *,
    session: SessionDep,
    _current_user: CurrentUser,
    status: str | None = None,
    task_type: str | None = None,
    queue: str | None = None,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """List all tasks across all users (superuser only)."""
    return crud.list_tasks(
        session=session,
        owner_id=None,
        status=status,
        task_type=task_type,
        queue=queue,
        skip=skip,
        limit=limit,
    )


# ---------------------------------------------------------------------------
# Legacy compatibility: job_id-based lookup
# ---------------------------------------------------------------------------


class LegacyJobStatusResponse(TaskPublic):
    """Backwards-compatible response that includes job_id alias."""

    job_id: str | None = None

    @classmethod
    def from_task(cls, task: Any) -> "LegacyJobStatusResponse":
        """Create a legacy response object from an existing task record."""
        data = TaskPublic.model_validate(task).model_dump()
        data["job_id"] = task.rq_job_id
        return cls(**data)


@router.get("/by-job/{job_id}", response_model=LegacyJobStatusResponse)
def get_task_by_job_id(
    job_id: str,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """Look up a task by its RQ job ID (legacy support)."""
    db_task = crud.get_task_by_rq_job_id(session=session, rq_job_id=job_id)
    if not db_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )
    if db_task.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )
    return LegacyJobStatusResponse.from_task(db_task)
