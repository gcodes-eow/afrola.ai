# Let's complete these final batches before we move to api-rest-flow

Batch 8: Error Handling & Dead Letter Queue
Files to create:

ai_engine/exceptions.py - Custom exceptions

jobs/models.py - FailedTask model

Failed Tasks Tracking:

python
class FailedTask(models.Model):
"""Store failed tasks for manual review"""
task_id = models.CharField(max_length=255, unique=True)
job = models.ForeignKey('jobs.Job', on_delete=models.CASCADE)
task_name = models.CharField(max_length=255)
error = models.TextField()
traceback = models.TextField()
retry_count = models.IntegerField(default=0)
created_at = models.DateTimeField(auto_now_add=True)
resolved = models.BooleanField(default=False)

Batch 9: Docker Setup
Dockerfile.celery:

dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY ai/ ./ai/

WORKDIR /app/backend

CMD ["celery", "-A", "config", "worker", "--loglevel=info"]
docker-compose.yml addition:

yaml
celery:
build:
context: ..
dockerfile: infra/docker/Dockerfile.celery
command: celery -A config worker --loglevel=info --concurrency=4
volumes: - ../backend:/app/backend - ../ai:/app/ai - ../storage:/app/storage
environment: - REDIS_URL=redis://redis:6379 - DJANGO_SETTINGS_MODULE=config.settings
depends_on: - redis - postgres

celery-beat:
build:
context: ..
dockerfile: infra/docker/Dockerfile.celery
command: celery -A config beat --loglevel=info
volumes: - ../backend:/app/backend
environment: - REDIS_URL=redis://redis:6379 - DJANGO_SETTINGS_MODULE=config.settings
depends_on: - redis - postgres

flower:
build:
context: ..
dockerfile: infra/docker/Dockerfile.celery
command: celery -A config flower --port=5555
ports: - "5555:5555"
environment: - REDIS_URL=redis://redis:6379
depends_on: - redis

Batch 10: Logging & Monitoring
Files to create:

ai_engine/logging.py - Task-specific logging

config/logging.py - Centralized logging config

Logging Configuration:

python
LOGGING = {
'celery': {
'handlers': ['file', 'console'],
'level': 'INFO',
'propagate': False,
},
'celery.task': {
'handlers': ['task_file'],
'level': 'INFO',
'formatter': 'verbose',
}
}
Queue Priority Matrix
Subscription Queue Concurrency Priority Notes
Enterprise high_priority 8 9 Dedicated workers
Pro high_priority 4 7 Shared pool
Free default 2 3 Lower priority
System scheduled 1 5 Beat tasks
Cleanup low_priority 1 1 Background
Task Retry Policy
Retry Delay Backoff
1 60 sec 1x
2 120 sec 2x
3 240 sec 4x
4+ Manual N/A
Dependencies
txt

# requirements.txt additions

celery==5.3.6
redis==5.0.1
django-celery-results==2.5.1
django-celery-beat==2.5.0
flower==2.0.1
Commands Reference
bash

# Development

celery -A config worker --loglevel=info
celery -A config beat --loglevel=info
celery -A config flower --port=5555

# Production (with queues)

celery -A config worker -Q high_priority --concurrency=8 --loglevel=info
celery -A config worker -Q default --concurrency=4 --loglevel=info
celery -A config worker -Q low_priority --concurrency=1 --loglevel=info

# Management

celery -A config purge -f # Purge all tasks
celery -A config inspect active # List active tasks
celery -A config inspect registered # List registered tasks
celery -A control revoke <task_id> # Revoke task
celery -A control revoke <task_id> --terminate # Terminate task

# Monitoring

celery -A config status # Worker status
celery -A config inspect stats # Worker statistics
celery -A config inspect scheduled # Scheduled tasks
Environment Variables
bash

# Celery

CELERY_BROKER_URL=redis://localhost:6379
CELERY_RESULT_BACKEND=redis://localhost:6379
CELERY_WORKER_CONCURRENCY=4
CELERY_TASK_ALWAYS_EAGER=False # True for testing (sync)

# Flower (monitoring)

FLOWER_PORT=5555
FLOWER_BASIC_AUTH=admin:password
Verification Checklist
Celery app loads without errors

Redis server is running (redis-cli ping)

Worker connects to Redis and starts

debug_task executes successfully

Tasks appear in Flower monitoring

Task status updates in database

Progress updates via cache work

Failed tasks retry properly

Dead letter queue stores failures

Periodic tasks run on schedule

Multiple workers process concurrently

Queue priorities respected

Results saved correctly

Email notifications sent on completion

Docker setup works with Celery

API Endpoints (for status checking)
Method Endpoint Description
GET /api/tasks/{task_id}/status/ Get Celery task status
GET /api/jobs/{job_id}/progress/ Get job progress via cache
POST /api/jobs/{job_id}/retry/ Manually retry failed job
DELETE /api/jobs/{job_id}/cancel/ Cancel pending/processing job
GET /api/workers/status/ Get worker status (admin)
