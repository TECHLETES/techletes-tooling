"""Tests for /admin/jobs/* endpoints (DB-backed task stats and listing)."""

import uuid
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from sqlmodel import Session

from backend import crud
from backend.core.config import settings
from backend.models import TaskCreate


def _stats_url() -> str:
    return f"{settings.API_V1_STR}/admin/jobs/stats"


def _list_url(
    queue: str | None = None, status_filter: str | None = None, limit: int = 50
) -> str:
    params: list[str] = [f"limit={limit}"]
    if queue:
        params.append(f"queue={queue}")
    if status_filter:
        params.append(f"status_filter={status_filter}")
    return f"{settings.API_V1_STR}/admin/jobs/list?" + "&".join(params)


def _mock_queue() -> MagicMock:
    fake_job = MagicMock()
    fake_job.id = str(uuid.uuid4())
    queue = MagicMock()
    queue.enqueue.return_value = fake_job
    return queue


def _create_task_in_db(
    db: Session,
    owner_id: uuid.UUID,
    task_type: str = "process_file",
    status: str = "queued",
) -> None:
    task_in = TaskCreate(task_type=task_type, queue="default", kwargs={"file_id": str(uuid.uuid4())})  # type: ignore[call-arg]
    db_task = crud.create_task(session=db, task_in=task_in, owner_id=owner_id)
    if status != "queued":
        crud.update_task_status(session=db, db_task=db_task, status=status)


# ---------------------------------------------------------------------------
# Stats endpoint
# ---------------------------------------------------------------------------


def test_stats_requires_superuser(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
) -> None:
    with patch("backend.api.routes.admin.get_redis_conn", return_value=MagicMock()):
        response = client.get(_stats_url(), headers=normal_user_token_headers)
    assert response.status_code == 403


def test_stats_returns_db_counts(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    """Stats should reflect DB task statuses."""
    from backend.tests.utils.user import create_random_user

    user = create_random_user(db)

    _create_task_in_db(db, user.id, status="queued")
    _create_task_in_db(db, user.id, status="completed")
    _create_task_in_db(db, user.id, status="failed")

    fake_conn = MagicMock()
    fake_q = MagicMock()
    fake_q.get_job_ids.return_value = []

    with (
        patch("backend.api.routes.admin.get_redis_conn", return_value=fake_conn),
        patch("backend.api.routes.admin.Queue", return_value=fake_q),
    ):
        response = client.get(_stats_url(), headers=superuser_token_headers)

    assert response.status_code == 200
    data = response.json()
    assert "status_counts" in data
    assert "queue_stats" in data
    assert "total_jobs" in data
    # We added at least 1 queued, 1 completed, 1 failed above
    assert data["status_counts"]["queued"] >= 1
    assert data["status_counts"]["completed"] >= 1
    assert data["status_counts"]["failed"] >= 1
    assert data["total_jobs"] >= 3


# ---------------------------------------------------------------------------
# List endpoint
# ---------------------------------------------------------------------------


def test_list_requires_superuser(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
) -> None:
    response = client.get(_list_url(), headers=normal_user_token_headers)
    assert response.status_code == 403


def test_list_returns_all_tasks(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    from backend.tests.utils.user import create_random_user

    user = create_random_user(db)
    _create_task_in_db(db, user.id, task_type="send_email")
    _create_task_in_db(db, user.id, task_type="export_data")

    response = client.get(_list_url(), headers=superuser_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert "jobs" in data
    assert "total" in data
    assert data["total"] >= 2


def test_list_status_filter(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    from backend.tests.utils.user import create_random_user

    user = create_random_user(db)
    _create_task_in_db(db, user.id, status="completed")
    _create_task_in_db(db, user.id, status="failed")

    response = client.get(
        _list_url(status_filter="completed"), headers=superuser_token_headers
    )
    assert response.status_code == 200
    data = response.json()
    for job in data["jobs"]:
        assert job["status"] == "completed"


def test_list_queue_filter(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    from backend.tests.utils.user import create_random_user

    user = create_random_user(db)
    task_in = TaskCreate(task_type="process_file", queue="high", kwargs={"file_id": "hf"})  # type: ignore[call-arg]
    crud.create_task(session=db, task_in=task_in, owner_id=user.id)

    response = client.get(_list_url(queue="high"), headers=superuser_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    for job in data["jobs"]:
        assert job["queue"] == "high"


def test_list_job_info_fields(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    """Each job in the list should have expected fields."""
    from backend.tests.utils.user import create_random_user

    user = create_random_user(db)
    _create_task_in_db(db, user.id)

    response = client.get(_list_url(limit=1), headers=superuser_token_headers)
    assert response.status_code == 200
    data = response.json()
    if data["jobs"]:
        job = data["jobs"][0]
        assert "id" in job
        assert "func" in job
        assert "status" in job
        assert "queue" in job
        assert "owner_id" in job
        assert "created_at" in job
