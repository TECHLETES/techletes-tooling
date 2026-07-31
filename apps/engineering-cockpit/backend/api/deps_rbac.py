"""Backwards-compatible RBAC dependency re-exports."""

from backend.api.deps import (
    permission_dep,
    require_all_permissions,
    require_any_role,
    require_permission,
    require_role,
)

__all__ = [
    "permission_dep",
    "require_all_permissions",
    "require_any_role",
    "require_permission",
    "require_role",
]
