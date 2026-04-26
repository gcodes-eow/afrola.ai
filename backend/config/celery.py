# backend/config/celery.py

import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('afrola')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


# ──────────────────────────────────────────────
# Periodic Tasks (Celery Beat Schedule)
# ──────────────────────────────────────────────

app.conf.beat_schedule = {
    'cleanup-old-jobs': {
        'task': 'ai_engine.tasks.cleanup_old_jobs_task',
        'schedule': crontab(hour=0, minute=0),  # Daily at midnight
        'args': (30,),  # Delete jobs older than 30 days
    },
    'reset-monthly-usage': {
        'task': 'accounts.tasks.reset_monthly_usage_task',
        'schedule': crontab(day_of_month='1', hour=0, minute=0),  # First of every month
    },
    'health-check': {
        'task': 'ai_engine.tasks.health_check_task',
        'schedule': crontab(minute='*/30'),  # Every 30 minutes
    },
}


@app.task(bind=True)
def debug_task(self):
    """Debug task to verify Celery is working"""
    print(f'Request: {self.request!r}')
    return 'Celery is working!'