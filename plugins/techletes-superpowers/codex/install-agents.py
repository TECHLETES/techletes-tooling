#!/usr/bin/env python3
"""Install native Codex roles without changing user configuration or permissions."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import sys
import tempfile
import tomllib

SOURCE = Path(__file__).resolve().parent / "agents"


def install(source: Path, destination: Path, *, overwrite: bool = False,
            dry_run: bool = False) -> list[str]:
    """Validate the entire bundle and collisions before writing any role files."""
    sources = sorted(source.glob("*.toml"))
    if not sources:
        raise ValueError(f"No agent TOML files in {source}")
    if destination.is_symlink():
        raise ValueError(f"Refusing symlink destination: {destination}")
    if destination.exists() and not destination.is_dir():
        raise ValueError(f"Destination is not a directory: {destination}")
    pending: list[tuple[Path, bytes]] = []
    messages: list[str] = []
    for path in sources:
        raw = path.read_bytes()
        data = tomllib.loads(raw.decode("utf-8"))
        if not path.stem.startswith("techletes-") or data.get("name") != path.stem:
            raise ValueError(f"Invalid role name: {path}")
        for key in ("name", "description", "developer_instructions", "model",
                    "model_reasoning_effort"):
            if not isinstance(data.get(key), str) or not data[key].strip():
                raise ValueError(f"Missing {key}: {path}")
        if data["model_reasoning_effort"] not in {"medium", "high", "xhigh"}:
            raise ValueError(f"Invalid reasoning effort: {path}")
        target = destination / path.name
        if target.is_symlink() or (target.exists() and not target.is_file()):
            raise ValueError(f"Refusing non-regular target: {target}")
        if target.exists() and target.read_bytes() == raw:
            messages.append(f"unchanged: {target}")
            continue
        if target.exists() and not overwrite:
            raise ValueError(f"Conflicting role: {target}; review it before using --overwrite")
        pending.append((target, raw))
    if dry_run:
        return messages + [f"would install: {path}" for path, _ in pending]
    if pending:
        destination.mkdir(parents=True, exist_ok=True)
    for target, raw in pending:
        if target.exists():
            fd, backup = tempfile.mkstemp(prefix=target.name + ".", suffix=".bak",
                                           dir=destination)
            os.close(fd)
            shutil.copy2(target, backup)
            messages.append(f"backup: {backup}")
        fd, temporary = tempfile.mkstemp(prefix=".techletes-", dir=destination)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(raw)
            os.replace(temporary, target)
        finally:
            Path(temporary).unlink(missing_ok=True)
        messages.append(f"installed: {target}")
    return messages


def main() -> int:
    """Parse arguments and report validation or filesystem failures clearly."""
    home = Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex").expanduser()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path, default=home / "agents")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--overwrite", action="store_true",
                        help="Replace differing roles, backing up each existing file")
    args = parser.parse_args()
    try:
        messages = install(SOURCE, args.destination.expanduser(),
                           overwrite=args.overwrite, dry_run=args.dry_run)
    except (OSError, ValueError) as error:
        parser.exit(1, f"error: {error}\n")
    print("\n".join(messages))
    return 0


if __name__ == "__main__":
    sys.exit(main())
