from unittest.mock import MagicMock, patch

from sqlmodel import select

from backend.utils.tests_pre_start import init, logger, main


def test_init_successful_connection() -> None:
    engine_mock = MagicMock()

    session_mock = MagicMock()
    session_mock.__enter__.return_value = session_mock

    select1 = select(1)

    with (
        patch("backend.utils.tests_pre_start.Session", return_value=session_mock),
        patch("backend.utils.tests_pre_start.select", return_value=select1),
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


def test_init_with_session_context_manager() -> None:
    """Test that init properly uses session context manager."""
    engine_mock = MagicMock()
    session_mock = MagicMock()
    session_context = MagicMock()
    session_context.__enter__.return_value = session_mock
    session_context.__exit__.return_value = None

    with (
        patch("backend.utils.tests_pre_start.Session", return_value=session_context),
        patch.object(logger, "info"),
        patch.object(logger, "error"),
    ):
        init(engine_mock)
        # Verify context manager was used
        session_context.__enter__.assert_called()
        session_context.__exit__.assert_called()


def test_main_calls_init() -> None:
    """Test that main function calls init."""
    with (
        patch("backend.utils.tests_pre_start.engine") as mock_engine,
        patch("backend.utils.tests_pre_start.init") as mock_init,
        patch.object(logger, "info"),
    ):
        main()
        mock_init.assert_called_once_with(mock_engine)
