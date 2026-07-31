"""Relationship configuration checks for SQLModel mappers."""

from sqlalchemy.orm import configure_mappers


def test_models_configure_mappers() -> None:
    """Importing the models must not leave broken relationship backrefs."""
    import backend.models  # noqa: F401

    configure_mappers()
