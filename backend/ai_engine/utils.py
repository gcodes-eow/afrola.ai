# backend/ai_engine/utils.py

from jobs.models import Job
from ai_engine.tasks import (
    process_audio_to_text_task,
    process_video_to_text_task,
    process_translation_task,
    process_subtitle_generation_task,
    create_dubbed_audio_task,
    create_dubbed_video_task,
    process_youtube_dubbing_task,
    _process_synchronously,
)


def trigger_job_processing(job):
    """Route job to the correct processing pipeline"""
    task_map = {
        'audio_to_text': process_audio_to_text_task,
        'video_to_text': process_video_to_text_task,
        'audio_to_audio': create_dubbed_audio_task,
        'video_to_audio': create_dubbed_audio_task,
        'video_to_video': create_dubbed_video_task,
        'youtube_to_video': process_youtube_dubbing_task,
    }

    task_func = task_map.get(job.job_type)
    if not task_func:
        raise ValueError(f"Unknown job type: {job.job_type}")

    # Process synchronously for now (replace with .delay() when Celery is configured)
    _process_synchronously(task_func, str(job.id))

    # Update job to queued
    from jobs.utils import update_job_status
    update_job_status(job, 'queued')
