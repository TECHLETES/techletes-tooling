#!/usr/bin/env python3
"""Validate branch names against the repo's allowed workflow conventions."""

from __future__ import annotations

import subprocess
import sys


ALLOWED_BARE_BRANCHES = ("main", "staging", "develop", "master")
ALLOWED_PREFIXES = (
    "feature/",
    "bug/",
    "refactor/",
    "security/",
    "breaking/",
    "question/",
    "docs/",
)


def _print_invalid(reason: str, branch_name: str | None) -> int:
    if branch_name:
        print(f"{branch_name} INVALID")
    else:
        print(f"INVALID: {reason}")
    print("Allowed bare branches:", ", ".join(ALLOWED_BARE_BRANCHES))
    print("Allowed prefixes:", ", ".join(ALLOWED_PREFIXES))
    return 1


def _resolve_branch_from_git() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return None

    if result.returncode != 0:
        return None

    branch_name = result.stdout.strip()
    if not branch_name or branch_name == "HEAD":
        return None
    return branch_name


def _is_allowed(branch_name: str) -> bool:
    if branch_name in ALLOWED_BARE_BRANCHES:
        return True
    return any(branch_name.startswith(prefix) for prefix in ALLOWED_PREFIXES)


def main(argv: list[str]) -> int:
    if len(argv) > 2:
        return _print_invalid("too many arguments", None)

    branch_name = argv[1] if len(argv) == 2 else _resolve_branch_from_git()
    if branch_name is None:
        return _print_invalid("no branch name available", None)

    if _is_allowed(branch_name):
        print(f"{branch_name} VALID")
        return 0

    return _print_invalid("branch name does not match allowed patterns", branch_name)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
