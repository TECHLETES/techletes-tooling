"""Allowlist checks for GitHub senders."""

from __future__ import annotations


def _coerce_allowlist(value: object) -> list[str]:
    if value is None:
        return []

    if isinstance(value, list):
        return [str(item) for item in value if str(item)]

    if isinstance(value, str):
        return [value]

    if isinstance(value, dict):
        for key in ("allowed_users", "users", "allowlist"):
            candidate = value.get(key)
            if isinstance(candidate, list):
                return [str(item) for item in candidate if str(item)]
            if isinstance(candidate, str) and candidate:
                return [candidate]

    return []


def is_user_allowed(
    username: str,
    allowed_users: list[str],
    event_name: str,
    event_auth: dict,
) -> bool:
    """Return True when the username is on the effective allowlist."""

    effective_allowlist = allowed_users
    if event_name in event_auth:
        effective_allowlist = _coerce_allowlist(event_auth.get(event_name))

    return username in effective_allowlist

