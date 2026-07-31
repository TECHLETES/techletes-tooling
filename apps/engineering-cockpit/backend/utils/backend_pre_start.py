"""Service startup utilities used before backend initialization."""

import logging
from typing import Any

from sqlalchemy import Engine
from sqlmodel import Session, select
from tenacity import after_log, before_log, retry, stop_after_attempt, wait_fixed

from backend.core.auth.entra import EntraAuthClient
from backend.core.config import settings
from backend.core.constants import constants
from backend.core.db import _seed_rbac, engine
from backend.core.rbac import DEFAULT_SYSTEM_ROLES, RoleDefinition

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

max_tries = 60 * 5  # 5 minutes
wait_seconds = 1


def _normalize_role_name(role_name: str) -> str:
    if (
        role_name.casefold() == settings.AZURE_SUPERUSER_ROLE.casefold()
        or role_name.casefold() == constants.roles.SUPER_ADMIN.casefold()
        or role_name.casefold() == constants.roles.ADMIN.casefold()
    ):
        return constants.roles.SUPER_ADMIN
    return role_name


def _build_role_definitions_from_entra(
    entra_roles: list[dict[str, Any]],
) -> dict[str, RoleDefinition]:
    """Map Entra app roles to local role definitions, preserving known permission sets."""
    role_definitions: dict[str, RoleDefinition] = {}

    for entra_role in entra_roles:
        raw_role_name = entra_role.get("value") or entra_role.get("displayName")
        if not isinstance(raw_role_name, str) or not raw_role_name.strip():
            continue

        role_name = _normalize_role_name(raw_role_name.strip())
        local_role = DEFAULT_SYSTEM_ROLES.get(role_name)
        role_description = entra_role.get("description")
        if not isinstance(role_description, str) or not role_description.strip():
            role_description = (
                local_role["description"] if local_role else f"{role_name} role"
            )

        role_definitions[role_name] = {
            "display_name": role_name,
            "description": role_description,
            "permissions": list(local_role["permissions"]) if local_role else [],
        }

    return role_definitions


def _get_startup_role_definitions() -> dict[str, RoleDefinition]:
    """Return role definitions for startup, preferring Entra app roles when available."""
    if not settings.azure_enabled:
        return DEFAULT_SYSTEM_ROLES

    logger.info("Loading roles from Microsoft Entra app registration...")
    entra_roles = EntraAuthClient().get_application_roles()
    if not entra_roles:
        logger.warning(
            "No Entra app roles found; falling back to local default system roles"
        )
        return DEFAULT_SYSTEM_ROLES

    role_definitions = _build_role_definitions_from_entra(entra_roles)
    if not role_definitions:
        logger.warning(
            "Entra app roles could not be normalized; falling back to local default system roles"
        )
        return DEFAULT_SYSTEM_ROLES

    logger.info("Loaded %s roles from Microsoft Entra", len(role_definitions))
    return role_definitions


@retry(
    stop=stop_after_attempt(max_tries),
    wait=wait_fixed(wait_seconds),
    before=before_log(logger, logging.INFO),
    after=after_log(logger, logging.WARN),
)
def init(db_engine: Engine) -> None:
    """Wait for the database to become available before starting the backend."""
    try:
        with Session(db_engine) as session:
            # Try to create session to check if DB is awake
            session.exec(select(1))
    except Exception as e:
        logger.error(e)
        raise e


def init_rbac(db_engine: Engine) -> None:
    """Initialize RBAC system with default permissions and roles."""
    try:
        with Session(db_engine) as session:
            role_definitions = _get_startup_role_definitions()
            logger.info("Synchronizing discovered RBAC permissions and system roles...")
            _seed_rbac(session, role_definitions)

    except Exception as e:
        logger.error(f"Failed to initialize RBAC: {e}")
        raise e


def main() -> None:
    """Initialize backend services and verify DB connectivity."""
    logger.info("Initializing service")
    # Only check DB connectivity here
    # RBAC initialization happens after migrations in initial_data.py
    init(engine)
    logger.info("Service finished initializing")


if __name__ == "__main__":
    main()
