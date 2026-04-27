

"""
Pipeline orchestration for AI processing tasks.
Supports sequential chains, parallel processing, and chord workflows.
"""
from celery import chain, group, chord
from django.core.cache import cache
from django.utils import timezone
from ai_engine.tasks import (
    process_text_to_text_task,
    process_audio_to_text_task,
    process_video_to_text_task,
    process_translation_task,
    process_subtitle_generation_task,
    create_dubbed_audio_task,
    create_dubbed_video_task,
    process_youtube_dubbing_task,
)


# ──────────────────────────────────────────────
# Progress Tracking (Real-time via cache)
# ──────────────────────────────────────────────

def update_progress(job_id, progress, step):
    """Store job progress in cache for real-time polling"""
    cache.set(f'job_progress_{job_id}', {
        'progress': progress,
        'step': step,
        'updated_at': timezone.now().isoformat()
    }, timeout=3600)


def get_progress(job_id):
    """Retrieve current job progress from cache"""
    return cache.get(f'job_progress_{job_id}', {'progress': 0, 'step': 'pending'})


def clear_progress(job_id):
    """Clear progress cache for a job"""
    cache.delete(f'job_progress_{job_id}')


# ──────────────────────────────────────────────
# Text → Text Pipelines
# ──────────────────────────────────────────────

text_to_text_pipeline = chain(
    process_text_to_text_task.s(),
    process_subtitle_generation_task.s(),
)

text_to_text_with_translation = chain(
    process_text_to_text_task.s(),
    process_translation_task.s(),
    process_subtitle_generation_task.s(),
)


# ──────────────────────────────────────────────
# Audio Pipelines
# ──────────────────────────────────────────────

audio_to_text_pipeline = chain(
    process_audio_to_text_task.s(),
)

audio_to_text_with_translation = chain(
    process_audio_to_text_task.s(),
    process_translation_task.s(),
)

audio_to_text_full = chain(
    process_audio_to_text_task.s(),
    process_translation_task.s(),
    process_subtitle_generation_task.s(),
)

audio_dubbing_pipeline = chain(
    process_audio_to_text_task.s(),
    process_translation_task.s(),
    process_subtitle_generation_task.s(),
    create_dubbed_audio_task.s(),
)


# ──────────────────────────────────────────────
# Video Pipelines
# ──────────────────────────────────────────────

video_to_text_pipeline = chain(
    process_video_to_text_task.s(),
)

video_to_text_full = chain(
    process_video_to_text_task.s(),
    process_translation_task.s(),
    process_subtitle_generation_task.s(),
)

video_dubbing_pipeline = chain(
    process_video_to_text_task.s(),
    process_translation_task.s(),
    process_subtitle_generation_task.s(),
    create_dubbed_video_task.s(),
)


# ──────────────────────────────────────────────
# YouTube Pipeline
# ──────────────────────────────────────────────

youtube_dubbing_pipeline = chain(
    process_youtube_dubbing_task.s(),
)


# ──────────────────────────────────────────────
# Parallel Processing (for splitting large files)
# ──────────────────────────────────────────────

def create_parallel_audio_pipeline(chunks):
    """
    Process audio chunks in parallel then merge results.
    chunks: list of (chunk_id, chunk_path) tuples
    """
    return chord(
        group(process_audio_to_text_task.s(chunk_id) for chunk_id, _ in chunks),
        process_translation_task.s()
    )


def create_parallel_video_pipeline(chunks):
    """
    Process video chunks in parallel then merge results.
    chunks: list of (chunk_id, chunk_path) tuples
    """
    return chord(
        group(process_video_to_text_task.s(chunk_id) for chunk_id, _ in chunks),
        process_translation_task.s()
    )


# ──────────────────────────────────────────────
# Pipeline Selector
# ──────────────────────────────────────────────

PIPELINE_MAP = {
    'text_to_text': text_to_text_with_translation,
    'audio_to_text': audio_to_text_full,
    'video_to_text': video_to_text_full,
    'audio_to_audio': audio_dubbing_pipeline,
    'video_to_audio': audio_dubbing_pipeline,
    'video_to_video': video_dubbing_pipeline,
    'youtube_to_video': youtube_dubbing_pipeline,
}


def get_pipeline(job_type, output_types=None):
    """
    Return the appropriate Celery chain for a given job type.
    
    Args:
        job_type: One of Job.TYPE_CHOICES
        output_types: List of requested outputs (optional, for future use)
    
    Returns:
        Celery chain or None if job_type not found
    """
    pipeline = PIPELINE_MAP.get(job_type)
    if not pipeline:
        return None

    # Future: Customize pipeline based on output_types
    # e.g., if 'subtitles' not in output_types, skip subtitle task

    return pipeline


def run_pipeline(job_type, job_id, output_types=None):
    """
    Execute the appropriate pipeline for a job.
    
    Args:
        job_type: One of Job.TYPE_CHOICES
        job_id: UUID of the job
        output_types: List of requested outputs
    
    Returns:
        AsyncResult from Celery
    """
    pipeline = get_pipeline(job_type, output_types)
    if not pipeline:
        raise ValueError(f"No pipeline defined for job type: {job_type}")

    update_progress(job_id, 0, 'Pipeline started')
    result = pipeline.delay(str(job_id))
    return result


# ──────────────────────────────────────────────
# Queue Assignment by Subscription
# ──────────────────────────────────────────────

def get_queue_for_user(user):
    """
    Determine which Celery queue to use based on subscription tier.
    
    Returns:
        str: Queue name ('high_priority', 'default', or 'low_priority')
    """
    if not user or not user.is_authenticated:
        return 'default'

    tier = user.subscription_tier
    if tier in ('pro', 'business'):
        return 'high_priority'
    return 'default'


def get_queue_for_job(job):
    """Get appropriate queue for a job based on its user's subscription"""
    return get_queue_for_user(job.user)


def get_priority_for_tier(subscription_tier):
    """
    Get numeric priority for subscription tier.
    Higher number = higher priority.
    """
    priorities = {
        'business': 9,
        'pro': 7,
        'free': 3,
    }
    return priorities.get(subscription_tier, 3)
