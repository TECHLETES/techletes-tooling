from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine
from testcontainers.postgres import PostgresContainer

# Import all models so SQLModel.metadata knows about every table
import backend.models  # noqa: F401
from backend.api.deps import get_db
from backend.core.config import settings
from backend.core.db import init_db
from backend.main import app
from backend.tests.utils.user import authentication_token_from_email
from backend.tests.utils.utils import get_superuser_token_headers


@pytest.fixture(scope="session")
def _postgres_container() -> Generator[PostgresContainer, None, None]:
    with PostgresContainer("postgres:18-alpine", driver="psycopg") as pg:
        yield pg


@pytest.fixture(scope="session")
def _engine(_postgres_container: PostgresContainer) -> Engine:
    url = _postgres_container.get_connection_url()
    engine = create_engine(url)
    SQLModel.metadata.create_all(engine)
    # Seed superuser once
    with Session(engine) as session:
        init_db(session)
    return engine


@pytest.fixture(autouse=True)
def db(_engine: Any) -> Generator[Session, None, None]:
    with Session(_engine) as session:
        yield session


@pytest.fixture(scope="module")
def client(_engine: Any) -> Generator[TestClient, None, None]:
    def _get_test_db() -> Generator[Session, None, None]:
        with Session(_engine) as session:
            yield session

    app.dependency_overrides[get_db] = _get_test_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture(scope="module")
def superuser_token_headers(client: TestClient) -> dict[str, str]:
    return get_superuser_token_headers(client)


@pytest.fixture(scope="module")
def normal_user_token_headers(client: TestClient, _engine: Any) -> dict[str, str]:
    with Session(_engine) as session:
        return authentication_token_from_email(
            client=client, email=settings.EMAIL_TEST_USER, db=session
        )


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    """Apply broad markers based on the test file location."""
    for item in items:
        item_path = Path(str(getattr(item, "path", item.fspath))).as_posix()

        if item_path.endswith("/backend/tests/test_utils.py"):
            item.add_marker(pytest.mark.unit)
            continue

        item.add_marker(pytest.mark.integration)

        if "/backend/tests/api/routes/" in item_path:
            item.add_marker(pytest.mark.api)
        elif item_path.endswith("/backend/tests/api/test_deps_rbac.py"):
            item.add_marker(pytest.mark.db)
        elif "/backend/tests/crud/" in item_path:
            item.add_marker(pytest.mark.db)
        elif "/backend/tests/scripts/" in item_path:
            item.add_marker(pytest.mark.slow)


@pytest.fixture(autouse=True)
def clear_testclient_cookies(client: TestClient) -> None:
    """Ensure no authentication cookies leak between tests by clearing them."""
    client.cookies.clear()
    # Remove any lingering Authorization header that may persist on TestClient
    client.headers.pop("Authorization", None)
    yield
    client.cookies.clear()
    client.headers.pop("Authorization", None)
