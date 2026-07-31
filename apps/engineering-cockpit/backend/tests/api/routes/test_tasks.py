"""Tests for /tasks endpoints."""

import uuid
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from sqlmodel import Session

from backend import crud
from backend.core.config import settings


def _enqueue_url() -> str:
    return f"{settings.API_V1_STR}/tasks/enqueue"


def _tasks_url() -> str:
    return f"{settings.API_V1_STR}/tasks/"


def _task_url(task_id: str) -> str:
    return f"{settings.API_V1_STR}/tasks/{task_id}"


def _all_tasks_url() -> str:
    return f"{settings.API_V1_STR}/tasks/admin/all"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_queue() -> MagicMock:
    """Return a mock RQ queue whose enqueue() returns a fake job."""
    fake_job = MagicMock()
    fake_job.id = str(uuid.uuid4())
    queue = MagicMock()
    queue.enqueue.return_value = fake_job
    return queue


# ---------------------------------------------------------------------------
# Enqueue
# ---------------------------------------------------------------------------


def test_enqueue_creates_db_record(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    """Enqueueing a task should create a DB record and return TaskPublic."""
    with patch("backend.api.routes.tasks.get_queue", return_value=_mock_queue()):
        response = client.post(
            _enqueue_url(),
            headers=superuser_token_headers,
            json={
                "task_type": "send_email",
                "queue": "default",
                "kwargs": {"to": "a@example.com", "subject": "hi", "_body": "body"},
            },
        )
    assert response.status_code == 200
    data = response.json()
    assert data["task_type"] == "send_email"
    assert data["queue"] == "default"
    assert data["status"] == "queued"
    assert "id" in data
    assert data["rq_job_id"] is not None

    # Verify DB record exists
    task_in_db = crud.get_task(session=db, task_id=uuid.UUID(data["id"]))
    assert task_in_db is not None
    assert task_in_db.status == "queued"


def test_enqueue_requires_auth(client: TestClient) -> None:
    """Unauthenticated requests should be rejected."""
    response = client.post(
        _enqueue_url(),
        json={"task_type": "send_email", "kwargs": {}},
    )
    assert response.status_code == 401


def test_enqueue_export_data(
    client: TestClient,
    superuser_token_headers: dict[str, str],
) -> None:
    with patch("backend.api.routes.tasks.get_queue", return_value=_mock_queue()):
        response = client.post(
            _enqueue_url(),
            headers=superuser_token_headers,
            json={
                "task_type": "export_data",
                "queue": "high",
                "kwargs": {"user_id": "u1", "format": "csv"},
            },
        )
    assert response.status_code == 200
    assert response.json()["task_type"] == "export_data"
    assert response.json()["queue"] == "high"


# ---------------------------------------------------------------------------
# List own tasks
# ---------------------------------------------------------------------------


def test_list_tasks_returns_own_only(
    client: TestClient,
    db: Session,
    superuser_token_headers: dict[str, str],
    normal_user_token_headers: dict[str, str],
) -> None:
    """Each user should only see their own tasks."""
    with patch("backend.api.routes.tasks.get_queue", return_value=_mock_queue()):
        # Superuser enqueues a task
        client.post(
            _enqueue_url(),
            headers=superuser_token_headers,
            json={"task_type": "process_file", "kwargs": {"file_id": "f1"}},
        )
        # Normal user enqueues a task
        client.post(
            _enqueue_url(),
            headers=normal_user_token_headers,
            json={"task_type": "process_file", "kwargs": {"file_id": "f2"}},
        )

    # Normal user should only see their own
    response = client.get(_tasks_url(), headers=normal_user_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["count"] >= 1
    # All returned tasks belong to the normal user
    for task in data["data"]:
        assert task["kwargs"]["file_id"] == "f2"


def test_list_tasks_status_filter(
    client: TestClient,
    superuser_token_headers: dict[str, str],
) -> None:
    """Status filter should narrow results."""
    with patch("backend.api.routes.tasks.get_queue", return_value=_mock_queue()):
        client.post(
            _enqueue_url(),
            headers=superuser_token_headers,
            json={
                "task_type": "send_email",
                "kwargs": {"to": "x@y.com", "subject": "s", "_body": "b"},
            },
        )

    response = client.get(
        _tasks_url() + "?status=queued", headers=superuser_token_headers
    )
    assert response.status_code == 200
    data = response.json()
    for task in data["data"]:
        assert task["status"] == "queued"

    response = client.get(
        _tasks_url() + "?status=completed", headers=superuser_token_headers
    )
    assert response.status_code == 200
    for task in response.json()["data"]:
        assert task["status"] == "completed"


# ---------------------------------------------------------------------------
# Get task by ID
# ---------------------------------------------------------------------------


def test_get_task_by_id(
    client: TestClient,
    superuser_token_headers: dict[str, str],
) -> None:
    with patch("backend.api.routes.tasks.get_queue", return_value=_mock_queue()):
        create_resp = client.post(
            _enqueue_url(),
            headers=superuser_token_headers,
            json={"task_type": "process_file", "kwargs": {"file_id": "abc"}},
        )
    task_id = create_resp.json()["id"]

    response = client.get(_task_url(task_id), headers=superuser_token_headers)
    assert response.status_code == 200
    assert response.json()["id"] == task_id


def test_get_task_not_found(
    client: TestClient,
    superuser_token_headers: dict[str, str],
) -> None:
    response = client.get(_task_url(str(uuid.uuid4())), headers=superuser_token_headers)
    assert response.status_code == 404


def test_get_task_wrong_user_is_forbidden(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    superuser_token_headers: dict[str, str],
) -> None:
    """A non-owner, non-superuser should get 403."""
    with patch("backend.api.routes.tasks.get_queue", return_value=_mock_queue()):
        create_resp = client.post(
            _enqueue_url(),
            headers=superuser_token_headers,
            json={"task_type": "process_file", "kwargs": {"file_id": "xyz"}},
        )
    task_id = create_resp.json()["id"]

    # Normal user cannot see superuser's task
    response = client.get(_task_url(task_id), headers=normal_user_token_headers)
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# Cancel task
# ---------------------------------------------------------------------------


def test_cancel_queued_task(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    with patch("backend.api.routes.tasks.get_queue", return_value=_mock_queue()):
        create_resp = client.post(
            _enqueue_url(),
            headers=superuser_token_headers,
            json={"task_type": "process_file", "kwargs": {"file_id": "cancel_me"}},
        )
    task_id = create_resp.json()["id"]

    with patch("backend.api.routes.tasks.Job") as mock_job_cls:
        mock_job_cls.fetch.return_value = MagicMock()
        response = client.delete(_task_url(task_id), headers=superuser_token_headers)

    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"

    # Verify DB was updated
    task_in_db = crud.get_task(session=db, task_id=uuid.UUID(task_id))
    assert task_in_db is not None
    assert task_in_db.status == "cancelled"


def test_cancel_completed_task_returns_conflict(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    """Cancelling an already-completed task should return 409."""
    with patch("backend.api.routes.tasks.get_queue", return_value=_mock_queue()):
        create_resp = client.post(
            _enqueue_url(),
            headers=superuser_token_headers,
            json={"task_type": "process_file", "kwargs": {"file_id": "done_file"}},
        )
    task_id = create_resp.json()["id"]

    # Manually complete it in DB
    task = crud.get_task(session=db, task_id=uuid.UUID(task_id))
    assert task is not None
    crud.update_task_status(session=db, db_task=task, status="completed")

    response = client.delete(_task_url(task_id), headers=superuser_token_headers)
    assert response.status_code == 409


# ---------------------------------------------------------------------------
# Admin: list all tasks
# ---------------------------------------------------------------------------


def test_list_all_tasks_superuser(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    normal_user_token_headers: dict[str, str],
) -> None:
    """Superuser /tasks/admin/all should see tasks from all users."""
    with patch("backend.api.routes.tasks.get_queue", return_value=_mock_queue()):
        client.post(
            _enqueue_url(),
            headers=superuser_token_headers,
            json={"task_type": "process_file", "kwargs": {"file_id": "su_file"}},
        )
        client.post(
            _enqueue_url(),
            headers=normal_user_token_headers,
            json={"task_type": "process_file", "kwargs": {"file_id": "nu_file"}},
        )

    response = client.get(_all_tasks_url(), headers=superuser_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["count"] >= 2


def test_list_all_tasks_normal_user_forbidden(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
) -> None:
    response = client.get(_all_tasks_url(), headers=normal_user_token_headers)
    assert response.status_code == 403
