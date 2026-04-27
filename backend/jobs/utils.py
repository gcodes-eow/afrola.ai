# backend/jobs/utils.py

from django.utils import timezone


def create_job_record(user, job_type, source_language, target_language,
                      source_file=None, youtube_url=None, source_text=None,
                      output_types=None, duration=None, file_size=None,
                      voice_model=None, add_background_music=False,
                      background_music_file=None, music_volume=0.3,
                      preserve_timestamps=True):
    """Create a new job record in the database"""
    from jobs.models import Job

    title = ''
    if source_file:
        title = source_file.name.split('/')[-1] if hasattr(source_file, 'name') else str(source_file)
    elif youtube_url:
        title = 'YouTube Video'
    elif source_text:
        title = source_text[:100]

    job = Job.objects.create(
        user=user,
        title=title,
        job_type=job_type,
        output_types=output_types or ['transcript', 'translation'],
        source_language=source_language,
        target_language=target_language,
        source_file=source_file,
        youtube_url=youtube_url,
        source_text=source_text or '',
        duration=duration,
        file_size=file_size,
        voice_model=voice_model,
        add_background_music=add_background_music,
        background_music_file=background_music_file,
        music_volume=music_volume,
        preserve_timestamps=preserve_timestamps,
        status='pending',
    )

    from dashboard.models import RecentActivity
    RecentActivity.objects.create(
        user=user,
        activity_type='job_created',
        description=f'Created {job.get_job_type_display()} job',
        job=job,
    )

    return job


def update_job_status(job, status, error_message='', processing_time=None):
    """Update job status with appropriate timestamps"""
    from django.utils import timezone

    job.status = status

    if status == 'queued':
        job.queued_at = timezone.now()
    elif status == 'processing':
        job.started_at = job.started_at or timezone.now()
    elif status == 'completed':
        job.completed_at = timezone.now()
    elif status == 'failed':
        job.error_message = error_message

    if processing_time:
        job.processing_time = processing_time

    job.save(update_fields=[
        'status', 'queued_at', 'started_at', 'completed_at',
        'error_message', 'processing_time'
    ])

    from dashboard.models import RecentActivity
    activity_map = {
        'completed': 'job_completed',
        'failed': 'job_failed',
    }
    if status in activity_map:
        RecentActivity.objects.create(
            user=job.user,
            activity_type=activity_map[status],
            description=f'Job {status}: {job.title}',
            job=job,
        )