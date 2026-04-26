# backend/ai_engine/tasks.py
import os
import logging
from celery import shared_task
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache
from jobs.models import Job
from jobs.utils import update_job_status
from ai_engine.models import AIModel, VoiceModel, ProcessingTask

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Helper: Run synchronously in development
# ──────────────────────────────────────────────

def _process_synchronously(task_func, job_id, *args, **kwargs):
    """Run task synchronously (for development without Celery workers).
    Replace with task_func.delay() in production."""
    logger.info(f"Processing job {job_id} synchronously (CELERY_TASK_ALWAYS_EAGER)")
    return task_func(job_id, *args, **kwargs)


def update_progress(job_id, progress, step):
    """Update job progress in cache for real-time polling"""
    cache.set(f'job_progress_{job_id}', {
        'progress': progress,
        'step': step,
        'updated_at': timezone.now().isoformat()
    }, timeout=3600)


# ──────────────────────────────────────────────
# Batch 3: Base Task with Retry Logic
# ──────────────────────────────────────────────

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_media_task(self, job_id):
    """Generic media processing task with retry logic"""
    job = Job.objects.get(id=job_id)

    try:
        update_job_status(job, 'processing')
        self.update_state(state='PROGRESS', meta={'step': 'starting', 'progress': 5})
        update_progress(job_id, 5, 'Starting processing...')

        # Route to the correct pipeline based on job type
        pipeline_map = {
            'text_to_text': _pipeline_text_to_text,
            'audio_to_text': _pipeline_audio_to_text,
            'video_to_text': _pipeline_video_to_text,
            'audio_to_audio': _pipeline_audio_to_audio,
            'video_to_audio': _pipeline_video_to_audio,
            'video_to_video': _pipeline_video_to_video,
            'youtube_to_video': _pipeline_youtube_to_video,
        }

        pipeline = pipeline_map.get(job.job_type)
        if not pipeline:
            raise ValueError(f"Unknown job type: {job.job_type}")

        result = pipeline(job, self)

        # Mark job complete
        update_job_status(job, 'completed', processing_time=result.get('processing_time'))
        update_progress(job_id, 100, 'Complete')

        return {'status': 'completed', 'job_id': str(job.id), 'results': result}

    except Exception as e:
        logger.error(f"Job {job_id} failed (attempt {self.request.retries + 1}): {e}")

        if self.request.retries < self.max_retries:
            countdown = 60 * (2 ** self.request.retries)  # Exponential backoff: 60, 120, 240
            update_job_status(job, 'pending', error_message=f"Retrying... ({self.request.retries + 1}/{self.max_retries})")
            raise self.retry(exc=e, countdown=countdown)

        # All retries exhausted
        update_job_status(job, 'failed', str(e))
        update_progress(job_id, 0, f'Failed: {str(e)[:100]}')
        return {'status': 'failed', 'error': str(e)}


# ──────────────────────────────────────────────
# Text → Text Task (NEW)
# ──────────────────────────────────────────────

@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def process_text_to_text_task(self, job_id):
    """Process text input — translate to target language"""
    job = Job.objects.get(id=job_id)
    task = _create_processing_task(job, 'translation')

    try:
        update_job_status(job, 'processing')
        self.update_state(state='PROGRESS', meta={'step': 'translating', 'progress': 20})
        update_progress(job_id, 20, 'Translating text...')

        # Use transcript as source text (should be set before creating job)
        source_text = job.transcript or ''
        if not source_text:
            # Set a placeholder if no transcript was provided (text input via form)
            source_text = job.transcript = f"[Text input for job {job_id}]"
            job.save(update_fields=['transcript'])

        # Translate — placeholder until NLLB model is integrated
        translation = (
            f"[Translation of job {job_id} from {job.source_language} "
            f"to {job.target_language} — AI model not yet integrated]\n"
            f"Source text length: {len(source_text)} characters."
        )
        job.translation = translation
        job.save(update_fields=['translation'])

        # If subtitles were requested
        if 'subtitles' in (job.output_types or []):
            self.update_state(state='PROGRESS', meta={'step': 'subtitles', 'progress': 60})
            update_progress(job_id, 60, 'Generating subtitles...')
            from utils.subtitle_generator import save_subtitle_file
            srt_content = (
                "1\n00:00:00,000 --> 00:00:05,000\n"
                f"{source_text[:200]}\n"
            )
            subtitle_path = save_subtitle_file(job, srt_content, 'srt')
            job.subtitle_file = subtitle_path
            job.save(update_fields=['subtitle_file'])

        update_job_status(job, 'completed', processing_time=(
            timezone.now() - job.started_at).total_seconds() if job.started_at else None
        )
        update_progress(job_id, 100, 'Complete')
        _complete_processing_task(task, {'translation': translation})

        return {'translation': translation}

    except Exception as e:
        logger.error(f"Text translation failed for job {job_id}: {e}")
        update_job_status(job, 'failed', str(e))
        _fail_processing_task(task, str(e))
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=30)
        raise


# ──────────────────────────────────────────────
# Audio → Text
# ──────────────────────────────────────────────

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_audio_to_text_task(self, job_id):
    """Convert audio to text transcript"""
    job = Job.objects.get(id=job_id)
    task = _create_processing_task(job, 'transcription')

    try:
        update_job_status(job, 'processing')
        self.update_state(state='PROGRESS', meta={'step': 'transcribing', 'progress': 20})
        update_progress(job_id, 20, 'Transcribing audio...')

        # TODO: Replace with actual Whisper model inference
        transcript = f"[Transcript for job {job_id} — AI model not yet integrated]"
        job.transcript = transcript
        job.save(update_fields=['transcript'])

        update_job_status(job, 'completed')
        update_progress(job_id, 100, 'Complete')
        _complete_processing_task(task, {'transcript': transcript})

        return {'transcript': transcript}

    except Exception as e:
        logger.error(f"Audio transcription failed for job {job_id}: {e}")
        update_job_status(job, 'failed', str(e))
        _fail_processing_task(task, str(e))
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
        raise


# ──────────────────────────────────────────────
# Video → Text
# ──────────────────────────────────────────────

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_video_to_text_task(self, job_id):
    """Extract audio from video and transcribe"""
    job = Job.objects.get(id=job_id)
    task = _create_processing_task(job, 'transcription')

    try:
        update_job_status(job, 'processing')
        self.update_state(state='PROGRESS', meta={'step': 'extracting_audio', 'progress': 10})
        update_progress(job_id, 10, 'Extracting audio from video...')

        # Extract audio
        from utils.ffmpeg_utils import extract_audio_from_video, get_media_duration
        if job.source_file:
            video_path = os.path.join(settings.MEDIA_ROOT, job.source_file.name)
            temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp', str(job.id))
            os.makedirs(temp_dir, exist_ok=True)
            audio_path = os.path.join(temp_dir, 'extracted_audio.mp3')
            extract_audio_from_video(video_path, audio_path)

        self.update_state(state='PROGRESS', meta={'step': 'transcribing', 'progress': 30})
        update_progress(job_id, 30, 'Transcribing audio...')

        transcript = f"[Video transcript for job {job_id} — AI model not yet integrated]"
        job.transcript = transcript
        job.save(update_fields=['transcript'])

        update_job_status(job, 'completed')
        update_progress(job_id, 100, 'Complete')
        _complete_processing_task(task, {'transcript': transcript})

        return {'transcript': transcript}

    except Exception as e:
        logger.error(f"Video transcription failed for job {job_id}: {e}")
        update_job_status(job, 'failed', str(e))
        _fail_processing_task(task, str(e))
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
        raise


# ──────────────────────────────────────────────
# Translation
# ──────────────────────────────────────────────

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_translation_task(self, job_id):
    """Translate transcript to target language"""
    job = Job.objects.get(id=job_id)
    task = _create_processing_task(job, 'translation')

    try:
        update_job_status(job, 'processing')
        self.update_state(state='PROGRESS', meta={'step': 'translating', 'progress': 40})
        update_progress(job_id, 40, 'Translating content...')

        translation = (
            f"[Translation of job {job_id} from {job.source_language} "
            f"to {job.target_language} — AI model not yet integrated]"
        )
        job.translation = translation
        job.save(update_fields=['translation'])

        update_job_status(job, 'completed')
        update_progress(job_id, 100, 'Complete')
        _complete_processing_task(task, {'translation': translation})

        return {'translation': translation}

    except Exception as e:
        logger.error(f"Translation failed for job {job_id}: {e}")
        update_job_status(job, 'failed', str(e))
        _fail_processing_task(task, str(e))
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
        raise


# ──────────────────────────────────────────────
# Subtitle Generation
# ──────────────────────────────────────────────

@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def process_subtitle_generation_task(self, job_id):
    """Generate subtitle files from transcript"""
    job = Job.objects.get(id=job_id)
    task = _create_processing_task(job, 'subtitle_generation')

    try:
        update_job_status(job, 'processing')
        self.update_state(state='PROGRESS', meta={'step': 'subtitles', 'progress': 60})
        update_progress(job_id, 60, 'Generating subtitles...')

        from utils.subtitle_generator import save_subtitle_file
        text = job.translation or job.transcript or '[No content]'
        srt_content = f"1\n00:00:00,000 --> 00:00:05,000\n{text[:500]}\n"
        subtitle_path = save_subtitle_file(job, srt_content, 'srt')
        job.subtitle_file = subtitle_path
        job.save(update_fields=['subtitle_file'])

        update_job_status(job, 'completed')
        update_progress(job_id, 100, 'Complete')
        _complete_processing_task(task, {'subtitle_path': subtitle_path})

        return {'subtitle_path': subtitle_path}

    except Exception as e:
        logger.error(f"Subtitle generation failed for job {job_id}: {e}")
        update_job_status(job, 'failed', str(e))
        _fail_processing_task(task, str(e))
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=30)
        raise


# ──────────────────────────────────────────────
# Dubbed Audio
# ──────────────────────────────────────────────

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def create_dubbed_audio_task(self, job_id, voice_id=None):
    """Generate dubbed audio from translated text"""
    job = Job.objects.get(id=job_id)
    task = _create_processing_task(job, 'tts_synthesis')

    try:
        update_job_status(job, 'processing')
        self.update_state(state='PROGRESS', meta={'step': 'synthesizing', 'progress': 70})
        update_progress(job_id, 70, 'Synthesizing speech...')

        voice = None
        if voice_id:
            voice = VoiceModel.objects.get(id=voice_id)
        elif job.voice_model:
            voice = VoiceModel.objects.filter(name=job.voice_model).first()

        audio_path = f"dubbed_audio/{job.id}/dubbed_audio.mp3"
        job.dubbed_audio = audio_path
        job.save(update_fields=['dubbed_audio'])

        update_job_status(job, 'completed')
        update_progress(job_id, 100, 'Complete')
        _complete_processing_task(task, {'audio_path': audio_path})

        return {'audio_path': audio_path}

    except Exception as e:
        logger.error(f"Dubbed audio creation failed for job {job_id}: {e}")
        update_job_status(job, 'failed', str(e))
        _fail_processing_task(task, str(e))
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
        raise


# ──────────────────────────────────────────────
# Dubbed Video
# ──────────────────────────────────────────────

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def create_dubbed_video_task(self, job_id, voice_id=None):
    """Replace audio track in video with dubbed version"""
    job = Job.objects.get(id=job_id)
    task = _create_processing_task(job, 'tts_synthesis')

    try:
        update_job_status(job, 'processing')
        self.update_state(state='PROGRESS', meta={'step': 'synthesizing', 'progress': 70})
        update_progress(job_id, 70, 'Creating dubbed audio...')

        create_dubbed_audio_task(job_id, voice_id)

        self.update_state(state='PROGRESS', meta={'step': 'merging', 'progress': 85})
        update_progress(job_id, 85, 'Merging audio with video...')

        video_path = f"dubbed_video/{job.id}/dubbed_video.mp4"
        job.dubbed_video = video_path
        job.save(update_fields=['dubbed_video'])

        update_job_status(job, 'completed')
        update_progress(job_id, 100, 'Complete')
        _complete_processing_task(task, {'video_path': video_path})

        return {'video_path': video_path}

    except Exception as e:
        logger.error(f"Dubbed video creation failed for job {job_id}: {e}")
        update_job_status(job, 'failed', str(e))
        _fail_processing_task(task, str(e))
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
        raise


# ──────────────────────────────────────────────
# YouTube Dubbing
# ──────────────────────────────────────────────

@shared_task(bind=True, max_retries=2, default_retry_delay=120)
def process_youtube_dubbing_task(self, job_id, voice_id=None):
    """Download YouTube video, transcribe, translate, dub"""
    job = Job.objects.get(id=job_id)
    task = _create_processing_task(job, 'transcription')

    try:
        update_job_status(job, 'processing')
        self.update_state(state='PROGRESS', meta={'step': 'downloading', 'progress': 5})
        update_progress(job_id, 5, 'Downloading YouTube video...')

        from utils.youtube_downloader import download_youtube_audio, get_youtube_info

        info = get_youtube_info(job.youtube_url)
        if info:
            job.title = info.get('title', job.title)
            job.duration = info.get('duration')
            job.save(update_fields=['title', 'duration'])

        temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp', str(job.id))
        os.makedirs(temp_dir, exist_ok=True)
        audio_path = os.path.join(temp_dir, 'downloaded_audio.mp3')
        downloaded_path, error = download_youtube_audio(job.youtube_url, audio_path)
        if error:
            raise Exception(f"YouTube download failed: {error}")

        process_audio_to_text_task(job_id)
        process_translation_task(job_id)
        process_subtitle_generation_task(job_id)
        create_dubbed_audio_task(job_id, voice_id)
        create_dubbed_video_task(job_id, voice_id)

        update_job_status(job, 'completed')
        update_progress(job_id, 100, 'Complete')
        _complete_processing_task(task, {'title': job.title})

        return {'title': job.title}

    except Exception as e:
        logger.error(f"YouTube dubbing failed for job {job_id}: {e}")
        update_job_status(job, 'failed', str(e))
        _fail_processing_task(task, str(e))
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=120 * (2 ** self.request.retries))
        raise


# ──────────────────────────────────────────────
# Cleanup & Maintenance Tasks
# ──────────────────────────────────────────────

@shared_task
def cleanup_old_jobs_task(days_old=30):
    """Delete jobs older than specified days and their files"""
    from django.utils import timezone
    cutoff = timezone.now() - timezone.timedelta(days=days_old)
    old_jobs = Job.objects.filter(created_at__lt=cutoff, status__in=['completed', 'failed', 'cancelled'])
    count = old_jobs.count()
    for job in old_jobs:
        if job.source_file:
            job.source_file.delete(save=False)
        if job.subtitle_file:
            job.subtitle_file.delete(save=False)
        if job.dubbed_audio:
            job.dubbed_audio.delete(save=False)
        if job.dubbed_video:
            job.dubbed_video.delete(save=False)
    old_jobs.delete()
    logger.info(f"Cleaned up {count} old jobs")
    return {'deleted': count}


@shared_task
def health_check_task():
    """Check that Celery and dependencies are working"""
    from django.db import connections
    from django.db.utils import OperationalError
    try:
        connections['default'].cursor()
        db_ok = True
    except OperationalError:
        db_ok = False

    return {
        'status': 'healthy',
        'database': db_ok,
        'timestamp': timezone.now().isoformat()
    }


# ──────────────────────────────────────────────
# Pipeline Orchestration
# ──────────────────────────────────────────────

def _pipeline_text_to_text(job, task):
    """Pipeline: Text → Translation"""
    task.update_state(state='PROGRESS', meta={'step': 'translating', 'progress': 30})
    process_translation_task(str(job.id))
    if 'subtitles' in (job.output_types or []):
        process_subtitle_generation_task(str(job.id))
    return {'output': job.translation}


def _pipeline_audio_to_text(job, task):
    """Pipeline: Audio → Transcript"""
    task.update_state(state='PROGRESS', meta={'step': 'transcribing', 'progress': 30})
    process_audio_to_text_task(str(job.id))
    if 'translation' in (job.output_types or []):
        process_translation_task(str(job.id))
    return {'output': job.transcript}


def _pipeline_video_to_text(job, task):
    """Pipeline: Video → Transcript"""
    task.update_state(state='PROGRESS', meta={'step': 'transcribing', 'progress': 30})
    process_video_to_text_task(str(job.id))
    if 'translation' in (job.output_types or []):
        process_translation_task(str(job.id))
    return {'output': job.transcript}


def _pipeline_audio_to_audio(job, task):
    """Pipeline: Audio → Dubbed Audio"""
    task.update_state(state='PROGRESS', meta={'step': 'transcribing', 'progress': 20})
    process_audio_to_text_task(str(job.id))
    task.update_state(state='PROGRESS', meta={'step': 'translating', 'progress': 50})
    process_translation_task(str(job.id))
    task.update_state(state='PROGRESS', meta={'step': 'synthesizing', 'progress': 80})
    create_dubbed_audio_task(str(job.id))
    return {'output': str(job.dubbed_audio)}


def _pipeline_video_to_audio(job, task):
    """Pipeline: Video → Dubbed Audio"""
    task.update_state(state='PROGRESS', meta={'step': 'extracting', 'progress': 15})
    process_video_to_text_task(str(job.id))
    task.update_state(state='PROGRESS', meta={'step': 'translating', 'progress': 50})
    process_translation_task(str(job.id))
    task.update_state(state='PROGRESS', meta={'step': 'synthesizing', 'progress': 80})
    create_dubbed_audio_task(str(job.id))
    return {'output': str(job.dubbed_audio)}


def _pipeline_video_to_video(job, task):
    """Pipeline: Video → Dubbed Video"""
    task.update_state(state='PROGRESS', meta={'step': 'extracting', 'progress': 15})
    process_video_to_text_task(str(job.id))
    task.update_state(state='PROGRESS', meta={'step': 'translating', 'progress': 50})
    process_translation_task(str(job.id))
    task.update_state(state='PROGRESS', meta={'step': 'synthesizing', 'progress': 80})
    create_dubbed_video_task(str(job.id))
    return {'output': str(job.dubbed_video)}


def _pipeline_youtube_to_video(job, task):
    """Pipeline: YouTube → Dubbed Video"""
    task.update_state(state='PROGRESS', meta={'step': 'downloading', 'progress': 10})
    process_youtube_dubbing_task(str(job.id))
    return {'output': str(job.dubbed_video)}


# ──────────────────────────────────────────────
# Processing Task Helpers
# ──────────────────────────────────────────────

def _create_processing_task(job, task_type):
    """Create a ProcessingTask record for tracking"""
    return ProcessingTask.objects.create(
        job=job,
        task_type=task_type,
        status='processing',
        started_at=timezone.now(),
    )


def _complete_processing_task(task, output_data):
    """Mark a ProcessingTask as completed"""
    task.status = 'completed'
    task.output_data = output_data
    task.completed_at = timezone.now()
    if task.started_at:
        task.processing_time = (task.completed_at - task.started_at).total_seconds()
    task.save()


def _fail_processing_task(task, error_message):
    """Mark a ProcessingTask as failed"""
    task.status = 'failed'
    task.error_message = error_message
    task.completed_at = timezone.now()
    if task.started_at:
        task.processing_time = (task.completed_at - task.started_at).total_seconds()
    task.save()
