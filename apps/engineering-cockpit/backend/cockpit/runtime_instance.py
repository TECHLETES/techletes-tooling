"""Host-level ownership lock for the Engineering Cockpit process."""

from __future__ import annotations

import fcntl
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, ClassVar

APPLICATION_VERSION = "0.1.0"
INHERITED_LOCK_FD_ENV = "COCKPIT_INHERITED_LOCK_FD"


def default_runtime_lock_path() -> Path:
    """Return the default path for the process ownership lock."""
    runtime_dir = os.environ.get("XDG_RUNTIME_DIR")
    if runtime_dir:
        return Path(runtime_dir) / "techletes-engineering-cockpit.lock"
    return Path.home() / ".cache" / "techletes-engineering-cockpit" / "instance.lock"


def runtime_lock_path() -> Path:
    """Return the configured or default path for the process ownership lock."""
    configured_lock_path = os.environ.get("COCKPIT_INSTANCE_LOCK_PATH")
    return (
        Path(configured_lock_path)
        if configured_lock_path
        else default_runtime_lock_path()
    )


class RuntimeInstanceAlreadyRunning(RuntimeError):
    """Raised when another process owns the cockpit runtime lock."""

    def __init__(self, path: Path, metadata: dict[str, Any] | None = None) -> None:
        """Initialize the error with the lock path and recorded metadata."""
        self.path = path
        self.metadata = metadata or {}
        pid = self.metadata.get("pid", "unknown")
        super().__init__(f"control plane already running (lock: {path}, pid: {pid})")


class RuntimeInstanceLock:
    """An OS-backed, process-lifetime lock for the cockpit control plane."""

    _file: Any
    _released: bool
    _application_version: ClassVar[str] = APPLICATION_VERSION

    def __init__(self, path: Path, file: Any) -> None:
        """Initialize a held runtime lock for ``path`` and its file handle."""
        self.path = path
        self._file = file
        self._released = False

    @classmethod
    def acquire(cls, path: Path) -> RuntimeInstanceLock:
        """Acquire an exclusive non-blocking lock at ``path``."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        file = path.open("a+")
        previous_metadata = cls._read_metadata(file)
        try:
            fcntl.flock(file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            metadata = cls._read_metadata(file)
            if not cls._pid_is_running(metadata.get("pid")):
                # A process exit releases flock, but retry once so stale
                # metadata cannot turn a recoverable lock into a false error.
                try:
                    fcntl.flock(file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    pass
                else:
                    return cls._write_metadata(path, file)
            file.close()
            raise RuntimeInstanceAlreadyRunning(path, metadata) from exc
        except BaseException:
            file.close()
            raise

        return cls._write_metadata(path, file, previous_metadata)

    @classmethod
    def acquire_for_lifespan(cls, path: Path) -> RuntimeInstanceLock:
        """Adopt a launcher lock or acquire one during application startup."""
        inherited_fd = os.environ.pop(INHERITED_LOCK_FD_ENV, None)
        if inherited_fd is None:
            return cls.acquire(path)
        try:
            file = os.fdopen(int(inherited_fd), "a+")
        except (OSError, ValueError) as exc:
            raise RuntimeError("invalid inherited cockpit runtime lock") from exc
        return cls._write_metadata(path, file)

    @classmethod
    def _write_metadata(
        cls,
        path: Path,
        file: Any,
        previous_metadata: dict[str, Any] | None = None,
    ) -> RuntimeInstanceLock:
        if previous_metadata:
            # Validate the recorded owner before replacing metadata. A dead
            # owner confirms this is stale and may be recovered.
            cls._pid_is_running(previous_metadata.get("pid"))
        metadata = {
            "pid": os.getpid(),
            "started_at": datetime.now(UTC).isoformat(),
            "application_version": cls._application_version,
        }
        file.seek(0)
        file.truncate()
        json.dump(metadata, file, separators=(",", ":"))
        file.write("\n")
        file.flush()
        os.fsync(file.fileno())
        return cls(path, file)

    @staticmethod
    def _pid_is_running(pid: object) -> bool:
        if not isinstance(pid, int) or pid <= 0:
            return False
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        return True

    @staticmethod
    def _read_metadata(file: Any) -> dict[str, Any]:
        file.seek(0)
        try:
            value = json.load(file)
        except (json.JSONDecodeError, OSError):
            return {}
        return value if isinstance(value, dict) else {}

    def release(self) -> None:
        """Release the lock and close its descriptor, leaving metadata behind."""
        if self._released:
            return
        self._released = True
        try:
            fcntl.flock(self._file.fileno(), fcntl.LOCK_UN)
        finally:
            self._file.close()

    def fileno(self) -> int:
        """Return the descriptor whose lifetime owns this process lock."""
        return int(self._file.fileno())

    def __enter__(self) -> RuntimeInstanceLock:
        """Return the held lock for use in a context manager."""
        return self

    def __exit__(self, *_: object) -> None:
        """Release the lock when leaving a context manager."""
        self.release()
