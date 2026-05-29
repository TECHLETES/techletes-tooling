"""Logging setup for the GitHub webhook proxy."""

from __future__ import annotations

import logging
from pathlib import Path


LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"


def configure_logging() -> logging.Logger:
    """Configure stdout and file logging once."""

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(LOG_FORMAT)

    has_stdout_handler = any(getattr(handler, "_github_proxy_stdout", False) for handler in logger.handlers)
    if not has_stdout_handler:
        stdout_handler = logging.StreamHandler()
        stdout_handler.setFormatter(formatter)
        stdout_handler._github_proxy_stdout = True  # type: ignore[attr-defined]
        logger.addHandler(stdout_handler)

    log_dir = Path.home() / ".hermes" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "github-proxy.log"
    has_file_handler = any(
        getattr(handler, "_github_proxy_file", False) and getattr(handler, "baseFilename", None) == str(log_path)
        for handler in logger.handlers
    )
    if not has_file_handler:
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(formatter)
        file_handler._github_proxy_file = True  # type: ignore[attr-defined]
        logger.addHandler(file_handler)

    return logger

