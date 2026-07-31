"""Admin endpoints for monitoring background jobs and queue statistics."""

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel
from rq import Queue
from sqlmodel import func, select

from backend.api.deps import CurrentUser, SessionDep, permission_dep
from backend.core.queue import get_redis_conn
from backend.models import Task

router = APIRouter(prefix="/admin", tags=["admin"])


# ---------------------------------------------------------------------------
# Response Models
# ---------------------------------------------------------------------------


class JobStatusCount(BaseModel):
    """Counts of jobs by status."""

    queued: int = 0
    running: int = 0
    completed: int = 0
    failed: int = 0
    cancelled: int = 0


class QueueStats(BaseModel):
    """Queue statistics entry for a single RQ queue."""

    name: str
    count: int


class JobInfo(BaseModel):
    """Metadata for a single background job."""

    id: str
    func: str
    status: str
    queue: str
    owner_id: str | None = None
    created_at: str | None = None
    started_at: str | None = None
    ended_at: str | None = None


class JobsStatsResponse(BaseModel):
    """Response schema for background job statistics."""

    status_counts: JobStatusCount
    queue_stats: list[QueueStats]
    total_jobs: int


class JobsListResponse(BaseModel):
    """Response schema for a list of background jobs."""

    jobs: list[JobInfo]
    total: int


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/jobs/stats",
    response_model=JobsStatsResponse,
    dependencies=permission_dep("admin:view_jobs"),
)
def get_jobs_stats(
    _current_user: CurrentUser,
    session: SessionDep,
) -> Any:
    """Get statistics about all background jobs.

    Status counts come from the DB (persistent history).
    Queue stats reflect the live RQ pending depth.
    """
    # DB-based status counts
    rows = session.exec(select(Task.status, func.count()).group_by(Task.status)).all()
    status_map: dict[str, int] = {row[0]: row[1] for row in rows}

    status_counts = JobStatusCount(
        queued=status_map.get("queued", 0),
        running=status_map.get("running", 0),
        completed=status_map.get("completed", 0),
        failed=status_map.get("failed", 0),
        cancelled=status_map.get("cancelled", 0),
    )
    total = sum(status_map.values())

    # Live queue depths from RQ
    conn = get_redis_conn()
    queue_stats = []
    for queue_name in ["high", "default", "low"]:
        q = Queue(queue_name, connection=conn)
        queue_stats.append(QueueStats(name=queue_name, count=len(q.get_job_ids())))

    return JobsStatsResponse(
        status_counts=status_counts,
        queue_stats=queue_stats,
        total_jobs=total,
    )


@router.get(
    "/jobs/list",
    response_model=JobsListResponse,
    dependencies=permission_dep("admin:manage_jobs"),
)
def get_jobs_list(
    _current_user: CurrentUser,
    session: SessionDep,
    queue: str | None = None,
    status_filter: str | None = None,
    limit: int = 50,
) -> Any:
    """List tasks from the DB.

    Query parameters:
    - queue: filter by queue name ("high", "default", "low")
    - status_filter: filter by status (queued, running, completed, failed, cancelled)
    - limit: max results to return (default 50)
    """
    from sqlmodel import col

    stmt = select(Task).order_by(col(Task.created_at).desc()).limit(limit)
    if queue:
        stmt = stmt.where(Task.queue == queue)
    if status_filter:
        stmt = stmt.where(Task.status == status_filter)

    tasks = session.exec(stmt).all()

    count_stmt = select(func.count()).select_from(Task)
    if queue:
        count_stmt = count_stmt.where(Task.queue == queue)
    if status_filter:
        count_stmt = count_stmt.where(Task.status == status_filter)
    total = session.exec(count_stmt).one()

    jobs_info = [
        JobInfo(
            id=str(t.id),
            func=t.task_type,
            status=t.status,
            queue=t.queue,
            owner_id=str(t.owner_id),
            created_at=t.created_at.isoformat() if t.created_at else None,
            started_at=t.started_at.isoformat() if t.started_at else None,
            ended_at=t.completed_at.isoformat() if t.completed_at else None,
        )
        for t in tasks
    ]

    return JobsListResponse(jobs=jobs_info, total=total)
