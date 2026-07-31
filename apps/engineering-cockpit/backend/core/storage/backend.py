"""File storage backends: local filesystem and S3-compatible object storage."""

from __future__ import annotations

import os
import shutil
import uuid
from abc import ABC, abstractmethod
from pathlib import Path

from backend.core.config import settings


class StorageBackend(ABC):
    """Abstract storage backend interface."""

    @abstractmethod
    def save(self, file_data: bytes, storage_key: str) -> str:
        """Persist file bytes under *storage_key*. Returns the storage key."""

    @abstractmethod
    def delete(self, storage_key: str) -> None:
        """Remove the object identified by *storage_key*."""

    @abstractmethod
    def get_download_url(self, storage_key: str, filename: str) -> str:
        """Return a URL to retrieve the file (presigned for S3, API URL for local)."""

    @abstractmethod
    def open(self, storage_key: str) -> bytes:
        """Return the raw bytes for the given storage key."""


class LocalStorage(StorageBackend):
    """Stores files on the local filesystem under *base_path*."""

    def __init__(self, base_path: str) -> None:
        """Initialize the local storage backend using the provided base path."""
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _full_path(self, storage_key: str) -> Path:
        return self.base_path / storage_key

    def save(self, file_data: bytes, storage_key: str) -> str:
        """Save file data to local storage and return the storage key."""
        full = self._full_path(storage_key)
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_bytes(file_data)
        return storage_key

    def delete(self, storage_key: str) -> None:
        """Delete a file identified by storage key from local storage."""
        path = self._full_path(storage_key)
        if path.exists():
            path.unlink()
        # Remove empty parent directories up to base_path
        parent = path.parent
        while parent != self.base_path:
            try:
                parent.rmdir()
            except OSError:
                break
            parent = parent.parent

    def get_download_url(self, storage_key: str, filename: str) -> str:
        """Return the API download URL for a locally stored file."""
        # Files are served through the FastAPI download endpoint
        file_id = storage_key.split("/")[0]
        return f"{settings.API_V1_STR}/files/{file_id}/download"

    def open(self, storage_key: str) -> bytes:
        """Read and return file bytes from local storage."""
        return self._full_path(storage_key).read_bytes()

    def copy_from_path(self, src: str, storage_key: str) -> str:
        """Copy a file from an existing local path into the storage directory."""
        dest = self._full_path(storage_key)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        return storage_key


class S3Storage(StorageBackend):
    """Stores files in an S3-compatible object store using boto3."""

    def __init__(self) -> None:
        """Initialize the S3 storage backend with configured AWS credentials."""
        try:
            import boto3
        except ImportError as exc:
            raise ImportError(
                "boto3 is required for S3 storage. Install it with: pip install boto3"
            ) from exc

        kwargs: dict[str, str] = {
            "aws_access_key_id": settings.AWS_ACCESS_KEY_ID,
            "aws_secret_access_key": settings.AWS_SECRET_ACCESS_KEY,
            "region_name": settings.S3_REGION,
        }
        if settings.S3_ENDPOINT_URL:
            kwargs["endpoint_url"] = settings.S3_ENDPOINT_URL

        self._client = boto3.client("s3", **kwargs)
        self._bucket = settings.S3_BUCKET_NAME

    def save(self, file_data: bytes, storage_key: str) -> str:
        """Upload file bytes to the configured S3 bucket."""
        self._client.put_object(
            Bucket=self._bucket,
            Key=storage_key,
            Body=file_data,
        )
        return storage_key

    def delete(self, storage_key: str) -> None:
        """Delete an object from the configured S3 bucket."""
        self._client.delete_object(Bucket=self._bucket, Key=storage_key)

    def get_download_url(self, storage_key: str, filename: str) -> str:
        """Return a presigned download URL for an S3 object."""
        url: str = self._client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": self._bucket,
                "Key": storage_key,
                "ResponseContentDisposition": f'attachment; filename="{filename}"',
            },
            ExpiresIn=3600,
        )
        return url

    def open(self, storage_key: str) -> bytes:
        """Read the bytes of an object from the configured S3 bucket."""
        response = self._client.get_object(Bucket=self._bucket, Key=storage_key)
        data: bytes = response["Body"].read()
        return data


def build_storage_key(file_id: uuid.UUID, filename: str) -> str:
    """Return a deterministic storage key for a file."""
    # Partition by first two chars of UUID to avoid large flat directories
    prefix = str(file_id)[:2]
    safe_name = os.path.basename(filename)
    return f"{prefix}/{file_id}/{safe_name}"


def get_storage() -> StorageBackend:
    """Return the configured storage backend (singleton-per-process is fine)."""
    if settings.STORAGE_BACKEND == "s3":
        return S3Storage()
    return LocalStorage(settings.LOCAL_STORAGE_PATH)
