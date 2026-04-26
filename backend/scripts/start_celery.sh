#!/bin/bash
QUEUE=${1:-"high_priority,default,low_priority,scheduled"}
CONCURRENCY=${2:-4}
LOGLEVEL=${3:-"info"}

echo "Starting Celery worker..."
echo "  Queues: $QUEUE"
echo "  Concurrency: $CONCURRENCY"

cd "$(dirname "$0")/.."
celery -A config worker --loglevel=$LOGLEVEL --concurrency=$CONCURRENCY --queues=$QUEUE --hostname=afrola-worker@%h
