"""RBAC configuration - Default roles and discovered permissions."""

import re
from functools import lru_cache
from pathlib import Path
from typing import TypedDict

from backend.core.constants import constants


class RoleDefinition(TypedDict):
    """Type definition for a system role."""

    display_name: str
    description: str
    permissions: list[str]


class PermissionDefinition(TypedDict):
    """Type definition for a permission."""

    name: str
    display: str
    resource: str


_BACKEND_PERMISSION_PATTERNS = (
    re.compile(r'require_permission\("([^"]+)"\)'),
    re.compile(r'permission_dep\("([^"]+)"\)'),
    re.compile(r"require_all_permissions\(([^\)]*)\)"),
)
_FRONTEND_PERMISSION_PATTERNS = (
    re.compile(r'can\("([^"]+)"\)'),
    re.compile(r"requiredPermissions:\s*\[([^\]]*)\]"),
)
_QUOTED_PERMISSION_PATTERN = re.compile(r'"([^"]+)"')


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _iter_permission_source_files() -> list[Path]:
    repo_root = _repo_root()
    return sorted(
        [
            *repo_root.joinpath("backend").rglob("*.py"),
            *repo_root.joinpath("frontend", "src").rglob("*.ts"),
            *repo_root.joinpath("frontend", "src").rglob("*.tsx"),
        ]
    )


def _extract_permissions_from_text(
    text: str, patterns: tuple[re.Pattern[str], ...]
) -> set[str]:
    permissions: set[str] = set()
    for pattern in patterns:
        for match in pattern.findall(text):
            captured = match if isinstance(match, str) else "".join(match)
            if pattern.pattern.endswith(r"\(([^\)]*)\)") or pattern.pattern.endswith(
                r"\[([^\]]*)\]"
            ):
                permissions.update(_QUOTED_PERMISSION_PATTERN.findall(captured))
            else:
                permissions.add(captured)
    return permissions


def _split_permission_name(permission_name: str) -> tuple[str, str] | None:
    if ":" in permission_name:
        return tuple(permission_name.split(":", maxsplit=1))  # type: ignore
    if "." in permission_name:
        return tuple(permission_name.rsplit(".", maxsplit=1))  # type: ignore
    return None


def _permission_display_name(permission_name: str) -> str:
    split_permission = _split_permission_name(permission_name)
    if split_permission is None:
        return permission_name
    resource, action = split_permission
    action_label = " ".join(part.capitalize() for part in action.split("_"))
    resource_label = " ".join(
        part.capitalize()
        for section in resource.split(".")
        for part in section.split("_")
    )
    return f"{action_label} {resource_label}"


@lru_cache(maxsize=1)
def discover_permissions() -> dict[str, list[PermissionDefinition]]:
    """Discover permissions from actual backend and frontend permission usage."""
    discovered_permissions: set[str] = set()

    for source_file in _iter_permission_source_files():
        if "/tests/" in source_file.as_posix():
            continue
        file_text = source_file.read_text(encoding="utf-8")
        patterns = (
            _BACKEND_PERMISSION_PATTERNS
            if source_file.suffix == ".py"
            else _FRONTEND_PERMISSION_PATTERNS
        )
        discovered_permissions.update(
            _extract_permissions_from_text(file_text, patterns)
        )

    grouped_permissions: dict[str, list[PermissionDefinition]] = {}
    for permission_name in sorted(discovered_permissions):
        split_permission = _split_permission_name(permission_name)
        if split_permission is None:
            continue
        resource, _action = split_permission
        grouped_permissions.setdefault(resource, []).append(
            {
                "name": permission_name,
                "display": _permission_display_name(permission_name),
                "resource": resource,
            }
        )

    return dict(sorted(grouped_permissions.items()))


# Discovered permissions catalog for the application.
DEFAULT_PERMISSIONS: dict[str, list[PermissionDefinition]] = discover_permissions()

# Default system roles - these are synced to Entra
DEFAULT_SYSTEM_ROLES: dict[str, RoleDefinition] = {
    constants.roles.VIEWER: {
        "display_name": constants.roles.VIEWER,
        "description": "Viewer can only view but not edit",
        "permissions": [
            "users:read",
            "reports:view",
            "items:read",
        ],
    },
    constants.roles.USER: {
        "display_name": constants.roles.USER,
        "description": "Users have normal usage rights",
        "permissions": [
            "users:read",
            "reports:view",
            "reports:download",
            "items:read",
            "items:create",
        ],
    },
    constants.roles.ADMIN: {
        "display_name": constants.roles.ADMIN,
        "description": "Admins have full access",
        "permissions": [
            "users:create",
            "users:read",
            "users:update",
            "users:delete",
            "users:manage_roles",
            "items:read",
            "items:create",
            "items:update",
            "items:delete",
            "reports:view",
            "reports:download",
            "reports:share",
            "rbac:view_permissions",
            "rbac:view_roles",
            "rbac:create_role",
            "rbac:update_role",
            "rbac:delete_role",
            "rbac:assign_permissions",
            "rbac:manage_users",
        ],
    },
    constants.roles.SUPER_ADMIN: {
        "display_name": constants.roles.SUPER_ADMIN,
        "description": "Super admins have full access to everything",
        "permissions": [],  # Super admins bypass all permission checks (see deps_rbac.py)
    },
}
