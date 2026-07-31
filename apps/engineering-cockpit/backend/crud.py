"""CRUD operations for backend models and user authentication."""

import uuid
from datetime import datetime
from typing import Any, cast

from sqlmodel import Session, col, func, select

from backend.core.auth.security import get_password_hash, verify_password
from backend.models import (
    Item,
    ItemCreate,
    Task,
    TaskCreate,
    TasksPublic,
    User,
    UserCreate,
    UserUpdate,
)


def create_user(*, session: Session, user_create: UserCreate) -> User:
    """Create a new user record with a hashed password."""
    db_obj = cast(
        User,
        User.model_validate(
            user_create,
            update={"hashed_password": get_password_hash(user_create.password)},
        ),
    )
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def update_user(*, session: Session, db_user: User, user_in: UserUpdate) -> User:
    """Update an existing user record."""
    user_data = user_in.model_dump(exclude_unset=True)
    extra_data = {}
    if "password" in user_data:
        password = user_data["password"]
        hashed_password = get_password_hash(password)
        extra_data["hashed_password"] = hashed_password
    db_user.sqlmodel_update(user_data, update=extra_data)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


def get_user_by_email(*, session: Session, email: str) -> User | None:
    """Return a user by email address, or None if not found."""
    statement = select(User).where(User.email == email)
    session_user = cast(User | None, session.exec(statement).first())
    return session_user


# Dummy hash to use for timing attack prevention when user is not found
# This is an Argon2 hash of a random password, used to ensure constant-time comparison
DUMMY_HASH = "$argon2id$v=19$m=65536,t=3,p=4$MjQyZWE1MzBjYjJlZTI0Yw$YTU4NGM5ZTZmYjE2NzZlZjY0ZWY3ZGRkY2U2OWFjNjk"


def authenticate(*, session: Session, email: str, password: str) -> User | None:
    """Authenticate a user by email and password."""
    db_user = get_user_by_email(session=session, email=email)
    if not db_user:
        # Prevent timing attacks by running password verification even when user doesn't exist
        # This ensures the response time is similar whether or not the email exists
        verify_password(password, DUMMY_HASH)
        return None
    verified, updated_password_hash = verify_password(password, db_user.hashed_password)
    if not verified:
        return None
    if updated_password_hash:
        db_user.hashed_password = updated_password_hash
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
    return db_user


def create_item(*, session: Session, item_in: ItemCreate, owner_id: uuid.UUID) -> Item:
    """Create a new item owned by the given user."""
    db_item = cast(Item, Item.model_validate(item_in, update={"owner_id": owner_id}))
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item


# ---------------------------------------------------------------------------
# Task CRUD
# ---------------------------------------------------------------------------


def create_task(*, session: Session, task_in: TaskCreate, owner_id: uuid.UUID) -> Task:
    """Create a new background task record."""
    db_task = cast(Task, Task.model_validate(task_in, update={"owner_id": owner_id}))
    session.add(db_task)
    session.commit()
    session.refresh(db_task)
    return db_task


def get_task(*, session: Session, task_id: uuid.UUID) -> Task | None:
    """Return a task record by its database ID."""
    return cast(Task | None, session.get(Task, task_id))


def get_task_by_rq_job_id(*, session: Session, rq_job_id: str) -> Task | None:
    """Return a task record by its RQ job ID."""
    statement = select(Task).where(Task.rq_job_id == rq_job_id)
    return cast(Task | None, session.exec(statement).first())


def update_task_status(
    *,
    session: Session,
    db_task: Task,
    status: str,
    rq_job_id: str | None = None,
    result: dict[str, Any] | None = None,
    error: str | None = None,
    started_at: datetime | None = None,
    completed_at: datetime | None = None,
) -> Task:
    """Update task metadata and persist status changes."""
    updates: dict[str, Any] = {"status": status}
    if rq_job_id is not None:
        updates["rq_job_id"] = rq_job_id
    if result is not None:
        updates["result"] = result
    if error is not None:
        updates["error"] = error
    if started_at is not None:
        updates["started_at"] = started_at
    if completed_at is not None:
        updates["completed_at"] = completed_at
    db_task.sqlmodel_update(updates)
    session.add(db_task)
    session.commit()
    session.refresh(db_task)
    return db_task


def list_tasks(
    *,
    session: Session,
    owner_id: uuid.UUID | None = None,
    status: str | None = None,
    task_type: str | None = None,
    queue: str | None = None,
    skip: int = 0,
    limit: int = 100,
) -> TasksPublic:
    """List tasks with optional filtering by owner, status, type, and queue, with pagination."""
    base_query = select(Task)
    count_query = select(func.count()).select_from(Task)

    filters = []
    if owner_id is not None:
        filters.append(Task.owner_id == owner_id)
    if status is not None:
        filters.append(Task.status == status)
    if task_type is not None:
        filters.append(Task.task_type == task_type)
    if queue is not None:
        filters.append(Task.queue == queue)

    for f in filters:
        base_query = base_query.where(f)
        count_query = count_query.where(f)

    count = session.exec(count_query).one()
    tasks = session.exec(
        base_query.order_by(col(Task.created_at).desc()).offset(skip).limit(limit)
    ).all()

    return TasksPublic(data=list(tasks), count=count)
