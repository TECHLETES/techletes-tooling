"""Tests for the process-lifetime cockpit instance lock."""

import json
import os
from pathlib import Path

import pytest

from backend.cockpit.runtime_instance import (
    RuntimeInstanceAlreadyRunning,
    RuntimeInstanceLock,
)


def test_second_instance_is_rejected(tmp_path: Path) -> None:
    first = RuntimeInstanceLock.acquire(tmp_path / "instance.lock")
    try:
        with pytest.raises(
            RuntimeInstanceAlreadyRunning, match="control plane already running"
        ):
            RuntimeInstanceLock.acquire(tmp_path / "instance.lock")
    finally:
        first.release()


def test_released_lock_can_be_reacquired(tmp_path: Path) -> None:
    path = tmp_path / "instance.lock"
    RuntimeInstanceLock.acquire(path).release()
    RuntimeInstanceLock.acquire(path).release()


def test_stale_metadata_is_recovered(tmp_path: Path) -> None:
    path = tmp_path / "instance.lock"
    path.write_text(
        json.dumps(
            {
                "pid": 999_999_999,
                "started_at": "2020-01-01T00:00:00+00:00",
                "application_version": "0.0.0",
            }
        )
    )

    lock = RuntimeInstanceLock.acquire(path)
    try:
        metadata = json.loads(path.read_text())
        assert metadata["pid"] == os.getpid()
        assert metadata["application_version"] == "0.1.0"
    finally:
        lock.release()
