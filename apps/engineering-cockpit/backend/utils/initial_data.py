"""Initial data seeding for first-run backend deployment."""

import logging

from sqlmodel import Session

from backend.core.db import engine, init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init() -> None:
    """Create initial database records and seed RBAC data."""
    with Session(engine) as session:
        init_db(session)


def main() -> None:
    """Run the initial data creation process."""
    logger.info("Creating initial data")
    init()
    logger.info("Initial data created")


if __name__ == "__main__":
    main()
