from unittest.mock import MagicMock, PropertyMock, patch

from sqlmodel import select

from backend.core.config import settings
from backend.core.constants import constants
from backend.core.rbac import DEFAULT_SYSTEM_ROLES
from backend.utils.backend_pre_start import init, init_rbac, logger, main


def test_init_successful_connection() -> None:
    engine_mock = MagicMock()

    session_mock = MagicMock()
    session_mock.__enter__.return_value = session_mock

    select1 = select(1)

    with (
        patch("backend.utils.backend_pre_start.Session", return_value=session_mock),
        patch("backend.utils.backend_pre_start.select", return_value=select1),
        patch.object(logger, "info"),
        patch.object(logger, "error"),
        patch.object(logger, "warn"),
    ):
        try:
            init(engine_mock)
            connection_successful = True
        except Exception:
            connection_successful = False

        assert (
            connection_successful
        ), "The database connection should be successful and not raise an exception."

        session_mock.exec.assert_called_once_with(select1)


def test_init_rbac_calls_shared_sync_with_default_roles() -> None:
    """Test that init_rbac delegates to the shared sync with local roles by default."""
    engine_mock = MagicMock()
    session_mock = MagicMock()
    session_mock.__enter__.return_value = session_mock

    with (
        patch("backend.utils.backend_pre_start.Session", return_value=session_mock),
        patch("backend.utils.backend_pre_start._seed_rbac") as mock_seed_rbac,
        patch.object(logger, "info"),
        patch.object(logger, "error"),
    ):
        init_rbac(engine_mock)
        role_definitions = mock_seed_rbac.call_args.args[1]
        assert constants.roles.SUPER_ADMIN in role_definitions


def test_init_rbac_uses_entra_role_definitions_when_configured() -> None:
    """Test that init_rbac passes normalized Entra role definitions to the shared sync."""
    engine_mock = MagicMock()
    session_mock = MagicMock()
    session_mock.__enter__.return_value = session_mock

    with (
        patch("backend.utils.backend_pre_start.Session", return_value=session_mock),
        patch("backend.utils.backend_pre_start._seed_rbac") as mock_seed_rbac,
        patch("backend.utils.backend_pre_start.settings.AZURE_CLIENT_ID", "test-id"),
        patch(
            "backend.utils.backend_pre_start.settings.AZURE_CLIENT_SECRET",
            "test-secret",
        ),
        patch.object(
            type(settings),
            "azure_enabled",
            new_callable=PropertyMock,
            return_value=True,
        ),
        patch("backend.utils.backend_pre_start.EntraAuthClient") as mock_entra,
        patch.object(logger, "info"),
    ):
        mock_entra_instance = MagicMock()
        mock_entra.return_value = mock_entra_instance
        mock_entra_instance.get_application_roles.return_value = [
            {
                "value": constants.roles.ADMIN,
                "displayName": constants.roles.ADMIN,
                "description": "Pulled from Entra",
                "isEnabled": True,
                "allowedMemberTypes": [constants.entra.APP_ROLE_MEMBER_TYPE_USER],
            }
        ]

        init_rbac(engine_mock)
        role_definitions = mock_seed_rbac.call_args.args[1]
        assert (
            role_definitions[constants.roles.SUPER_ADMIN]["description"]
            == "Pulled from Entra"
        )
        assert set(role_definitions) == {constants.roles.SUPER_ADMIN}


def test_init_rbac_falls_back_to_default_roles_when_entra_empty() -> None:
    """Test that init_rbac still delegates with local defaults when Entra returns none."""
    engine_mock = MagicMock()
    session_mock = MagicMock()
    session_mock.__enter__.return_value = session_mock

    with (
        patch("backend.utils.backend_pre_start.Session", return_value=session_mock),
        patch("backend.utils.backend_pre_start.settings.AZURE_CLIENT_ID", "test-id"),
        patch(
            "backend.utils.backend_pre_start.settings.AZURE_CLIENT_SECRET",
            "test-secret",
        ),
        patch.object(
            type(settings),
            "azure_enabled",
            new_callable=PropertyMock,
            return_value=True,
        ),
        patch("backend.utils.backend_pre_start.EntraAuthClient") as mock_entra,
        patch("backend.utils.backend_pre_start._seed_rbac") as mock_seed_rbac,
        patch.object(logger, "info"),
        patch.object(logger, "warning"),
    ):
        mock_entra_instance = MagicMock()
        mock_entra.return_value = mock_entra_instance
        mock_entra_instance.get_application_roles.return_value = []

        init_rbac(engine_mock)
        role_definitions = mock_seed_rbac.call_args.args[1]
        assert role_definitions == DEFAULT_SYSTEM_ROLES


def test_init_rbac_exception_handling() -> None:
    """Test that init_rbac handles exceptions gracefully."""
    engine_mock = MagicMock()
    session_mock = MagicMock()
    session_mock.__enter__.return_value = session_mock
    session_mock.exec.side_effect = Exception("DB Error")

    with (
        patch("backend.utils.backend_pre_start.Session", return_value=session_mock),
        patch.object(logger, "error"),
    ):
        try:
            init_rbac(engine_mock)
            raised = False
        except Exception:
            raised = True

        assert raised, "init_rbac should raise exception on DB error"


def test_main_calls_init_and_init_rbac() -> None:
    """Test that main function calls init (RBAC init happens in initial_data.py)."""
    with (
        patch("backend.utils.backend_pre_start.engine") as mock_engine,
        patch("backend.utils.backend_pre_start.init") as mock_init,
        patch.object(logger, "info"),
    ):
        main()
        mock_init.assert_called_once_with(mock_engine)
