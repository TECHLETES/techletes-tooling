"""Host-level ownership lock for the Engineering Cockpit process."""

from __future__ import annotations

import fcntl
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, ClassVar

APPLICATION_VERSION = "0.1.0"


class RuntimeInstanceAlreadyRunning(RuntimeError):
    """Raised when another process owns the cockpit runtime lock."""

    def __init__(self, path: Path, metadata: dict[str, Any] | None = None) -> None:
        self.path = path
        self.metadata = metadata or {}
        pid = self.metadata.get("pid", "unknown")
        super().__init__(
            f"control plane already running (lock: {path}, pid: {pid})"
        )


class RuntimeInstanceLock:
    """An OS-backed, process-lifetime lock for the cockpit control plane."""

    _file: Any
    _released: bool
    _application_version: ClassVar[str] = APPLICATION_VERSION

    def __init__(self, path: Path, file: Any) -> None:
        self.path = path
        self._file = file
        self._released = False

    @classmethod
    def acquire(cls, path: Path) -> RuntimeInstanceLock:
        """Acquire an exclusive non-blocking lock at ``path``."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
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

    def __enter__(self) -> RuntimeInstanceLock:
        return self

    def __exit__(self, *_: object) -> None:
        self.release()
