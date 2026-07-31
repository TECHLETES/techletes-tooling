"""File upload / download endpoints."""

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import Response
from sqlmodel import col, func, select

from backend.api.deps import CurrentUser, SessionDep, permission_dep
from backend.core.storage.backend import build_storage_key, get_storage
from backend.models import File, FilePublic, FilesPublic, Message

router = APIRouter(prefix="/files", tags=["files"])

# 50 MB default upload limit
MAX_UPLOAD_BYTES = 50 * 1024 * 1024


@router.post(
    "/",
    response_model=FilePublic,
    dependencies=permission_dep("files:upload"),
)
def upload_file(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    file: UploadFile,
) -> Any:
    """Upload a file. Returns file metadata."""
    data = file.file.read()

    if len(data) > MAX_UPLOAD_BYTES:
        max_mb = MAX_UPLOAD_BYTES // (1024 * 1024)
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds maximum size of {max_mb} MB",
        )

    file_id = uuid.uuid4()
    filename = file.filename or "upload"
    content_type = file.content_type or "application/octet-stream"
    storage_key = build_storage_key(file_id, filename)

    storage = get_storage()
    storage.save(data, storage_key)

    db_file = File(
        id=file_id,
        filename=filename,
        content_type=content_type,
        size=len(data),
        storage_key=storage_key,
        owner_id=current_user.id,
    )
    session.add(db_file)
    session.commit()
    session.refresh(db_file)
    return db_file


@router.get(
    "/",
    response_model=FilesPublic,
    dependencies=permission_dep("files:read"),
)
def list_files(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """List files owned by the current user (superusers see all)."""
    if current_user.is_superuser:
        count = session.exec(select(func.count()).select_from(File)).one()
        files = session.exec(
            select(File).order_by(col(File.created_at).desc()).offset(skip).limit(limit)
        ).all()
    else:
        count = session.exec(
            select(func.count())
            .select_from(File)
            .where(File.owner_id == current_user.id)
        ).one()
        files = session.exec(
            select(File)
            .where(File.owner_id == current_user.id)
            .order_by(col(File.created_at).desc())
            .offset(skip)
            .limit(limit)
        ).all()

    return FilesPublic(data=list(files), count=count)


@router.get(
    "/{id}",
    response_model=FilePublic,
    dependencies=permission_dep("files:read"),
)
def get_file(
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
) -> Any:
    """Return file metadata."""
    db_file = session.get(File, id)
    if not db_file:
        raise HTTPException(status_code=404, detail="File not found")
    if not current_user.is_superuser and db_file.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return db_file


@router.get(
    "/{id}/download",
    dependencies=permission_dep("files:download"),
)
def download_file(
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
) -> Response:
    """Stream file bytes to the client."""
    db_file = session.get(File, id)
    if not db_file:
        raise HTTPException(status_code=404, detail="File not found")
    if not current_user.is_superuser and db_file.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    storage = get_storage()
    data = storage.open(db_file.storage_key)

    return Response(
        content=data,
        media_type=db_file.content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{db_file.filename}"',
            "Content-Length": str(db_file.size),
        },
    )


@router.delete(
    "/{id}",
    dependencies=permission_dep("files:delete"),
)
def delete_file(
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
) -> Message:
    """Delete a file and its stored data."""
    db_file = session.get(File, id)
    if not db_file:
        raise HTTPException(status_code=404, detail="File not found")
    if not current_user.is_superuser and db_file.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    storage = get_storage()
    storage.delete(db_file.storage_key)

    session.delete(db_file)
    session.commit()
    return Message(message="File deleted successfully")
