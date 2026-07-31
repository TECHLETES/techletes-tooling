"""Tests for the process-lifetime cockpit instance lock."""

import json
import multiprocessing
import os
from pathlib import Path
from typing import Any

import pytest

from backend.cockpit.runtime_instance import (
    RuntimeInstanceAlreadyRunning,
    RuntimeInstanceLock,
)


def _hold_lock(path: str, ready: Any) -> None:
    lock = RuntimeInstanceLock.acquire(Path(path))
    ready.set()
    ready.wait()
    lock.release()


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


def test_lock_is_recovered_after_owner_process_exits(tmp_path: Path) -> None:
    path = tmp_path / "instance.lock"
    context = multiprocessing.get_context("spawn")
    ready = context.Event()
    owner = context.Process(target=_hold_lock, args=(str(path), ready))
    owner.start()
    try:
        assert ready.wait(5)
        owner_pid = owner.pid
    finally:
        owner.terminate()
        owner.join(5)

    assert not RuntimeInstanceLock._pid_is_running(owner_pid)
    lock = RuntimeInstanceLock.acquire(path)
    try:
        metadata = json.loads(path.read_text())
        assert metadata["pid"] == os.getpid()
        assert metadata["pid"] != owner_pid
    finally:
        lock.release()


def test_lifespan_can_adopt_launcher_lock_descriptor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "instance.lock"
    launcher_lock = RuntimeInstanceLock.acquire(path)
    inherited_fd = os.dup(launcher_lock.fileno())
    monkeypatch.setenv("COCKPIT_INHERITED_LOCK_FD", str(inherited_fd))

    lifespan_lock = RuntimeInstanceLock.acquire_for_lifespan(path)
    try:
        with pytest.raises(RuntimeInstanceAlreadyRunning):
            RuntimeInstanceLock.acquire(path)
    finally:
        lifespan_lock.release()
        launcher_lock.release()
