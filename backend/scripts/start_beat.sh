#!/bin/bash
# Start Celery Beat scheduler for Afrola.ai
# Usage: ./scripts/start_beat.sh

echo "Starting Celery Beat scheduler..."
cd "$(dirname "$0")/.."
celery -A config beat --loglevel=info --scheduler=django_celery_beat.schedulers:DatabaseScheduler
