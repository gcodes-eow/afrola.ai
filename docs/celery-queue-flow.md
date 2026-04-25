docs/celery-queue-flow.md

# Celery Queue Flow — Afrola.ai (Django + Celery)

## Purpose
Define how async media processing jobs (transcription, translation, audio dubbing, video dubbing) are queued, executed, and monitored using Celery and Redis.

## Flow Overview
Job Create → Queue → Worker → Process → Complete → Callback
↓ ↓ ↓ ↓ ↓ ↓
Database Redis Celery AI Task Results Notify

text

## Architecture Components

| Component | Location | Purpose |
|-----------|----------|---------|
| Celery App | `config/celery.py` | Celery configuration |
| Task Definition | `ai_engine/tasks.py` | Async processing tasks |
| Task Queue | Redis | Message broker |
| Result Backend | Django DB | Store task results |
| Worker Process | `celery worker` | Execute tasks |
| Beat Scheduler | `celery beat` | Periodic tasks |
| Flower | Optional | Task monitoring UI |
| Progress Tracking | Redis/Cache | Real-time progress updates |

## Required Files

### Celery Configuration
backend/config/
├── init.py # ✅ Import celery app
├── celery.py # ⏳ Celery app definition
└── settings.py # ✅ Celery settings (broker, backend)

text

### AI Engine Tasks
backend/ai_engine/
├── init.py # ✅
├── tasks.py # ⏳ All processing tasks
├── callbacks.py # ⏳ Success/failure callbacks
├── utils.py # ⏳ Task helpers (progress updates)
└── views.py # ⏳ Task status views

text

### Account Tasks
backend/accounts/
├── tasks.py # ⏳ User-related tasks (cleanup, reset)
├── signals.py # ⏳ Post-save signals for tasks
└── utils.py # ⏳ Email notification helpers

text

### Jobs App
backend/jobs/
├── models.py # ✅ Job model with status tracking
├── utils.py # ⏳ Job helpers (progress calculation)
└── admin.py # ✅ Job admin with task inspection

text

### Worker Management
scripts/
├── start_celery.sh # ⏳ Start worker script
├── start_beat.sh # ⏳ Start beat scheduler
├── monitor_celery.py # ⏳ Health check script
└── restart_celery.sh # ⏳ Restart all workers

infra/docker/
├── Dockerfile.celery # ⏳ Celery worker container
├── docker-compose.yml # ✅ Include celery service
└── docker-compose.prod.yml # ✅ Production celery service

text

### Monitoring
infra/prometheus/
├── celery_exporter.yml # ⏳ Celery metrics exporter
└── alerts.yml # ⏳ Alerting rules

infra/grafana/
└── dashboards/
└── celery_dashboard.json # ⏳ Celery monitoring dashboard

text

## Implementation Plan

### Batch 1: Celery Setup
**Files to create:**
- `config/celery.py` - Celery app definition
- `config/settings.py` - Add Celery configuration
- `scripts/start_celery.sh` - Worker startup script

**Celery Configuration:**
```python
# config/celery.py
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
app = Celery('afrola')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
Settings:

python
# Celery Configuration
CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')
CELERY_RESULT_BACKEND = 'django-db'
CELERY_CACHE_BACKEND = 'django-cache'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_WORKER_MAX_TASKS_PER_CHILD = 100

Batch 2: Task Definition
Files to create:

ai_engine/tasks.py - All processing tasks

ai_engine/callbacks.py - Task callbacks

ai_engine/utils.py - Progress helpers

Task Types:

Task Name	Purpose	Input	Output	Priority
process_audio_text_task	Transcribe audio to text	audio_file_path, source_lang	transcript	High
process_video_text_task	Extract audio, transcribe video	video_file_path, source_lang	transcript	High
process_audio_dubbing_task	Transcribe, translate, synthesize	audio_file_path, source_lang, target_lang, voice	dubbed_audio	High
process_video_dubbing_task	Full video dubbing pipeline	video_file_path, source_lang, target_lang, voice, music	dubbed_video	High
process_youtube_task	Download and process YouTube	youtube_url, source_lang, target_lang, options	dubbed_video	Medium
process_translation_task	Translate existing transcript	job_id, target_lang	translation	Medium
generate_subtitles_task	Generate subtitle file	job_id, format	subtitle_file	Low
cleanup_old_jobs_task	Delete old jobs and files	days_old	None	Low
reset_monthly_usage_task	Reset usage counters	None	None	Low
send_notification_task	Email/SMS notifications	user_id, message	None	Low

Batch 3: Task Implementation with Retry Logic
Files to create:

ai_engine/tasks.py - Complete task implementations

ai_engine/callbacks.py - on_success, on_failure, on_retry

Base Task Pattern:

python
@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_media_task(self, job_id):
    job = Job.objects.get(id=job_id)
    
    try:
        # Update status
        job.status = 'processing'
        job.started_at = timezone.now()
        job.save()
        
        # Update progress (for real-time UI)
        self.update_state(state='PROGRESS', meta={'current': 1, 'total': 5, 'step': 'transcribing'})
        update_progress(job_id, 20, 'Transcribing audio...')
        
        # Call AI pipeline based on job_type
        if job.job_type == 'audio_to_text':
            result = process_audio_transcription(job)
        elif job.job_type == 'audio_to_audio':
            result = process_audio_dubbing(job)
        elif job.job_type == 'video_to_video':
            result = process_video_dubbing(job)
        elif job.job_type == 'youtube_to_video':
            result = process_youtube_dubbing(job)
        
        # Save results
        save_job_results(job, result)
        
        # Send completion notification
        send_completion_notification.delay(job.user.id, job.id)
        
        return {'status': 'completed', 'job_id': str(job.id), 'results': result}
        
    except Exception as e:
        logger.error(f"Job {job_id} failed: {str(e)}")
        
        # Update job status
        job.status = 'failed'
        job.error_message = str(e)
        job.save()
        
        # Retry if possible
        if self.request.retries < self.max_retries:
            countdown = 60 * (2 ** self.request.retries)  # Exponential backoff
            raise self.retry(exc=e, countdown=countdown)
        
        # Send failure notification
        send_failure_notification.delay(job.user.id, job.id, str(e))
        
        return {'status': 'failed', 'error': str(e)}

Batch 4: Task Chaining & Parallel Processing
Files to create:

ai_engine/pipeline.py - Pipeline orchestration

Task Chains:

python
from celery import chain, group, chord

# Sequential chain (for simple workflows)
audio_pipeline = chain(
    transcribe_audio_task.s(),
    translate_text_task.s(),
    generate_subtitles_task.s()
)

# Parallel processing (for large files)
split_audio_task.s() | group(
    transcribe_chunk_task.s(chunk) for chunk in chunks
) | merge_transcripts_task.s()

# Chord (wait for all parallel tasks)
chord(
    group(process_chunk_task.s(chunk) for chunk in chunks),
    aggregate_results_task.s()
)
Progress Tracking:

python
# Real-time progress via Redis
def update_progress(job_id, progress, step):
    cache.set(f'job_progress_{job_id}', {
        'progress': progress,
        'step': step,
        'updated_at': timezone.now().isoformat()
    }, timeout=3600)
Batch 5: Queue Priority System
Queue Configuration:

python
# settings.py
CELERY_TASK_ROUTES = {
    'ai_engine.tasks.process_audio_text_task': {'queue': 'high_priority'},
    'ai_engine.tasks.process_video_text_task': {'queue': 'high_priority'},
    'ai_engine.tasks.process_audio_dubbing_task': {'queue': 'high_priority'},
    'ai_engine.tasks.process_video_dubbing_task': {'queue': 'high_priority'},
    'ai_engine.tasks.process_youtube_task': {'queue': 'default'},
    'ai_engine.tasks.generate_subtitles_task': {'queue': 'low_priority'},
    'accounts.tasks.reset_monthly_usage_task': {'queue': 'scheduled'},
}

# Queue priorities (0-9, higher = more urgent)
CELERY_TASK_DEFAULT_PRIORITY = 5
CELERY_TASK_QUEUE_MAX_PRIORITY = 10
Queue Assignment by Subscription:

python
def get_queue_for_user(user):
    if user.subscription.is_pro:
        return 'high_priority'
    if user.subscription.is_enterprise:
        return 'high_priority'
    return 'default'

Batch 6: Monitoring with Flower
Files to create:

scripts/start_flower.sh - Flower startup script

ai_engine/views.py - Task status API

Flower Setup:

bash
# Install Flower
pip install flower

# Run Flower
celery -A config flower --port=5555 --basic_auth=admin:password

# Access at http://localhost:5555
Task Status API:

python
@api_view(['GET'])
def task_status(request, task_id):
    """Get Celery task status"""
    result = AsyncResult(task_id)
    return Response({
        'status': result.status,
        'result': result.result if result.ready() else None,
        'traceback': result.traceback if result.failed() else None
    })

Batch 7: Periodic Tasks (Celery Beat)
Files to create:

config/celery.py - Beat schedule

accounts/tasks.py - User cleanup tasks

jobs/tasks.py - Job cleanup tasks

Beat Schedule:

python
# config/celery.py
from celery.schedules import crontab

app.conf.beat_schedule = {
    'cleanup-old-jobs': {
        'task': 'jobs.tasks.cleanup_old_jobs_task',
        'schedule': crontab(hour=0, minute=0),  # Daily at midnight
        'args': (30,)  # Delete jobs older than 30 days
    },
    'reset-monthly-usage': {
        'task': 'accounts.tasks.reset_monthly_usage_task',
        'schedule': crontab(day_of_month='1', hour=0, minute=0),  # First of month
    },
    'send-usage-warnings': {
        'task': 'accounts.tasks.send_usage_warnings',
        'schedule': crontab(hour=12, minute=0),  # Daily at noon
    },
    'retry-failed-jobs': {
        'task': 'jobs.tasks.retry_failed_jobs',
        'schedule': crontab(hour='*/6'),  # Every 6 hours
    },
    'health-check': {
        'task': 'ai_engine.tasks.health_check_task',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
    },
}

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
  volumes:
    - ../backend:/app/backend
    - ../ai:/app/ai
    - ../storage:/app/storage
  environment:
    - REDIS_URL=redis://redis:6379
    - DJANGO_SETTINGS_MODULE=config.settings
  depends_on:
    - redis
    - postgres

celery-beat:
  build:
    context: ..
    dockerfile: infra/docker/Dockerfile.celery
  command: celery -A config beat --loglevel=info
  volumes:
    - ../backend:/app/backend
  environment:
    - REDIS_URL=redis://redis:6379
    - DJANGO_SETTINGS_MODULE=config.settings
  depends_on:
    - redis
    - postgres

flower:
  build:
    context: ..
    dockerfile: infra/docker/Dockerfile.celery
  command: celery -A config flower --port=5555
  ports:
    - "5555:5555"
  environment:
    - REDIS_URL=redis://redis:6379
  depends_on:
    - redis
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
Subscription	Queue	Concurrency	Priority	Notes
Enterprise	high_priority	8	9	Dedicated workers
Pro	high_priority	4	7	Shared pool
Free	default	2	3	Lower priority
System	scheduled	1	5	Beat tasks
Cleanup	low_priority	1	1	Background
Task Retry Policy
Retry	Delay	Backoff
1	60 sec	1x
2	120 sec	2x
3	240 sec	4x
4+	Manual	N/A
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
celery -A config purge -f                      # Purge all tasks
celery -A config inspect active                # List active tasks
celery -A config inspect registered            # List registered tasks
celery -A control revoke <task_id>             # Revoke task
celery -A control revoke <task_id> --terminate # Terminate task

# Monitoring
celery -A config status                        # Worker status
celery -A config inspect stats                 # Worker statistics
celery -A config inspect scheduled             # Scheduled tasks
Environment Variables
bash
# Celery
CELERY_BROKER_URL=redis://localhost:6379
CELERY_RESULT_BACKEND=redis://localhost:6379
CELERY_WORKER_CONCURRENCY=4
CELERY_TASK_ALWAYS_EAGER=False  # True for testing (sync)

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
Method	Endpoint	Description
GET	/api/tasks/{task_id}/status/	Get Celery task status
GET	/api/jobs/{job_id}/progress/	Get job progress via cache
POST	/api/jobs/{job_id}/retry/	Manually retry failed job
DELETE	/api/jobs/{job_id}/cancel/	Cancel pending/processing job
GET	/api/workers/status/	Get worker status (admin)
Related Documentation
docs/file-upload-flow.md - Triggers Celery tasks after upload

docs/user-auth-flow.md - User context for tasks

docs/subscription-flow.md - Queue priority by subscription

docs/database-schema.md - Job and task models

docs/api-rest-flow.md - Task status endpoints