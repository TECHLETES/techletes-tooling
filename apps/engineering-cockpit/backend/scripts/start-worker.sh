#!/bin/bash
# Start the RQ worker for background task processing
# This script can be run in development or production to start the job queue worker

set -e

echo "🚀 Starting RQ Worker..."
echo "   Processing jobs from: high, default, low queues (in priority order)"
echo ""
echo "💡 Tip: You can enqueue jobs via POST /api/v1/tasks/enqueue"
echo "       Check job status via GET /api/v1/tasks/{job_id}"
echo ""

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
export PYTHONPATH="${repo_root}${PYTHONPATH:+:$PYTHONPATH}"

cd "${repo_root}/backend"

# Start the worker
echo "⚙️  Starting worker..."
uv run python -m backend.worker
