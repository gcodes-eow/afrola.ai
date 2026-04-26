# backend/ai_engine/callbacks.py
import logging
from jobs.models import Job
from dashboard.models import RecentActivity

logger = logging.getLogger(__name__)


def on_task_success(job_id, result):
    """Called when a Celery task completes successfully"""
    try:
        job = Job.objects.get(id=job_id)
        logger.info(f"Job {job_id} completed successfully")

        RecentActivity.objects.create(
            user=job.user,
            activity_type='job_completed',
            description=f'Job completed: {job.title}',
            job=job,
        )
    except Job.DoesNotExist:
        logger.error(f"Job {job_id} not found in on_task_success callback")


def on_task_failure(job_id, exception, traceback):
    """Called when a Celery task fails"""
    try:
        job = Job.objects.get(id=job_id)
        logger.error(f"Job {job_id} failed: {exception}")

        job.status = 'failed'
        job.error_message = str(exception)
        job.retry_count += 1
        job.save()

        RecentActivity.objects.create(
            user=job.user,
            activity_type='job_failed',
            description=f'Job failed: {job.title}',
            job=job,
        )
    except Job.DoesNotExist:
        logger.error(f"Job {job_id} not found in on_task_failure callback")


def on_task_retry(job_id, retry_count, exception):
    """Called when a Celery task is retried"""
    try:
        job = Job.objects.get(id=job_id)
        logger.warning(f"Job {job_id} retry {retry_count}: {exception}")

        job.retry_count = retry_count
        job.error_message = f"Retry {retry_count}: {exception}"
        job.save(update_fields=['retry_count', 'error_message'])
    except Job.DoesNotExist:
        logger.error(f"Job {job_id} not found in on_task_retry callback")
