"""Example background tasks.

Each function here is a regular Python function (no async) that can be
enqueued with ``queue.enqueue(task_fn, *args, **kwargs)``.

Real tasks should import from ``backend.core`` as needed; these examples
log progress so the worker output is visible.
"""

from __future__ import annotations

import logging
import time

logger = logging.getLogger(__name__)


def send_email_task(
    to: str, subject: str, _body: str, _task_id: str | None = None
) -> dict[str, str]:
    """Simulate sending a transactional email in the background.

    In production, replace the body with actual email-sending logic using
    the backend email utilities (``backend.utils.send_email``).
    """
    logger.info("Sending email to %s | subject: %s", to, subject)
    # Simulate I/O latency
    time.sleep(0.5)
    logger.info("Email sent to %s", to)
    return {"status": "sent", "to": to, "subject": subject}


def export_data_task(
    user_id: str, format: str = "csv", _task_id: str | None = None
) -> dict[str, str]:
    """Simulate a long-running data export.

    Replace with real DB queries and file generation; write the result to
    the file storage backend (``backend.core.storage.get_storage()``) and
    notify the user when done via the notification pub/sub channel.
    """
    logger.info("Starting data export for user %s (format=%s)", user_id, format)
    # Simulate heavy processing
    time.sleep(2)
    filename = f"export_{user_id}.{format}"
    logger.info("Export complete: %s", filename)
    return {"status": "complete", "filename": filename}


def process_file_task(file_id: str, _task_id: str | None = None) -> dict[str, str]:
    """Simulate post-upload file processing (e.g. thumbnail generation, OCR).

    Replace with real processing logic; load the file via
    ``backend.core.storage.get_storage().open(storage_key)`` and update
    the ``File`` record in the DB when done.
    """
    logger.info("Processing file %s", file_id)
    # Simulate processing time
    time.sleep(1)
    logger.info("File %s processed successfully", file_id)
    return {"status": "processed", "file_id": file_id}
