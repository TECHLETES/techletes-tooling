"""RQ worker entry point.

Run with:
    python worker.py

Or via Docker Compose (``worker`` service). The worker processes jobs from
the ``high``, ``default``, and ``low`` queues in priority order.
"""

import logging

from rq import Worker

from backend.core.queue import get_redis_conn

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

if __name__ == "__main__":
    conn = get_redis_conn()
    queues = ["high", "default", "low"]
    worker = Worker(queues, connection=conn)
    worker.work(with_scheduler=True)
