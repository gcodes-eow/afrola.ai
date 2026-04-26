# backend/ai_engine/tasks.py

import os
import logging
from celery import shared_task
from django.conf import settings
from django.utils import timezone
from jobs.models import Job
from jobs.utils import update_job_status
from ai_engine.models import AIModel, VoiceModel, ProcessingTask

logger = logging.getLogger(__name__)


def _process_synchronously(task_func, job_id, *args, **kwargs):
    """
    Run task synchronously (for development without Celery workers).
    Replace with celery_task.delay() in production.
    """
    logger.info(f"Processing job {job_id} synchronously (Celery not configured)")
    return task_func(job_id, *args, **kwargs)


@shared_task
def process_audio_to_text_task(job_id):
    """Convert audio to text transcript"""
    job = Job.objects.get(id=job_id)
    task = _create_processing_task(job, 'transcription')

    try:
        update_job_status(job, 'processing')

        # Placeholder: Simulate transcription
        # TODO: Replace with actual Whisper model inference
        transcript = f"[Transcript for job {job_id} — AI model not yet integrated]"
        job.transcript = transcript

        update_job_status(job, 'completed')
        _complete_processing_task(task, {'transcript': transcript})

    except Exception as e:
        logger.error(f"Transcription failed for job {job_id}: {e}")
        update_job_status(job, 'failed', str(e))
        _fail_processing_task(task, str(e))
        raise


@shared_task
def process_video_to_text_task(job_id):
    """Convert video to text transcript"""
    job = Job.objects.get(id=job_id)
    task = _create_processing_task(job, 'transcription')

    try:
        update_job_status(job, 'processing')

        # Extract audio first (handled by pipeline)
        # Placeholder: Simulate transcription
        transcript = f"[Video transcript for job {job_id} — AI model not yet integrated]"
        job.transcript = transcript

        update_job_status(job, 'completed')
        _complete_processing_task(task, {'transcript': transcript})

    except Exception as e:
        logger.error(f"Video transcription failed for job {job_id}: {e}")
        update_job_status(job, 'failed', str(e))
        _fail_processing_task(task, str(e))
        raise


@shared_task
def process_translation_task(job_id):
    """Translate transcript to target language"""
    job = Job.objects.get(id=job_id)
    task = _create_processing_task(job, 'translation')

    try:
        update_job_status(job, 'processing')

        # Translate transcription
        # TODO: Replace with actual NLLB model inference
        translation = (
            f"[Translation of job {job_id} from {job.source_language} "
            f"to {job.target_language} — AI model not yet integrated]"
        )
        job.translation = translation

        update_job_status(job, 'completed')
        _complete_processing_task(task, {'translation': translation})

    except Exception as e:
        logger.error(f"Translation failed for job {job_id}: {e}")
        update_job_status(job, 'failed', str(e))
        _fail_processing_task(task, str(e))
        raise


@shared_task
def process_subtitle_generation_task(job_id):
    """Generate subtitle files from transcript with timestamps"""
    job = Job.objects.get(id=job_id)
    task = _create_processing_task(job, 'subtitle_generation')

    try:
        update_job_status(job, 'processing')

        # Generate subtitles
        # TODO: Replace with actual subtitle generation
        srt_content = (
            "1\n00:00:00,000 --> 00:00:05,000\n"
            "[Subtitles pending — AI model not yet integrated]\n"
        )
        from utils.subtitle_generator import save_subtitle_file
        subtitle_path = save_subtitle_file(job, srt_content, 'srt')
        job.subtitle_file = subtitle_path

        update_job_status(job, 'completed')
        _complete_processing_task(task, {'subtitle_path': subtitle_path})

    except Exception as e:
        logger.error(f"Subtitle generation failed for job {job_id}: {e}")
        update_job_status(job, 'failed', str(e))
        _fail_processing_task(task, str(e))
        raise


@shared_task
def create_dubbed_audio_task(job_id, voice_id=None):
    """Generate dubbed audio from translated text"""
    job = Job.objects.get(id=job_id)
    task = _create_processing_task(job, 'tts_synthesis')

    try:
        update_job_status(job, 'processing')

        # Get voice model
        voice = None
        if voice_id:
            voice = VoiceModel.objects.get(id=voice_id)
        elif job.voice_model:
            voice = VoiceModel.objects.filter(name=job.voice_model).first()

        # Synthesize speech
        # TODO: Replace with actual Coqui TTS inference
        audio_path = f"dubbed_audio/{job.id}/dubbed_audio.mp3"
        job.dubbed_audio = audio_path

        update_job_status(job, 'completed')
        _complete_processing_task(task, {'audio_path': audio_path})

    except Exception as e:
        logger.error(f"Dubbed audio creation failed for job {job_id}: {e}")
        update_job_status(job, 'failed', str(e))
        _fail_processing_task(task, str(e))
        raise


@shared_task
def create_dubbed_video_task(job_id, voice_id=None):
    """Replace audio track in video with dubbed version"""
    job = Job.objects.get(id=job_id)
    task = _create_processing_task(job, 'tts_synthesis')

    try:
        update_job_status(job, 'processing')

        # First generate dubbed audio
        create_dubbed_audio_task(job_id, voice_id)

        # Merge audio with video
        # TODO: Replace with actual ffmpeg merge
        video_path = f"dubbed_video/{job.id}/dubbed_video.mp4"
        job.dubbed_video = video_path

        update_job_status(job, 'completed')
        _complete_processing_task(task, {'video_path': video_path})

    except Exception as e:
        logger.error(f"Dubbed video creation failed for job {job_id}: {e}")
        update_job_status(job, 'failed', str(e))
        _fail_processing_task(task, str(e))
        raise


@shared_task
def process_youtube_dubbing_task(job_id, voice_id=None):
    """Download YouTube video and process for dubbing"""
    job = Job.objects.get(id=job_id)
    task = _create_processing_task(job, 'transcription')

    try:
        update_job_status(job, 'processing')

        # Download YouTube audio
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

        # Transcribe
        process_audio_to_text_task(job_id)

        # Translate
        process_translation_task(job_id)

        # Generate subtitles
        process_subtitle_generation_task(job_id)

        # Generate dubbed audio
        create_dubbed_audio_task(job_id, voice_id)

        # Generate dubbed video (audio + static image or original)
        create_dubbed_video_task(job_id, voice_id)

        update_job_status(job, 'completed')
        _complete_processing_task(task, {'title': job.title})

    except Exception as e:
        logger.error(f"YouTube dubbing failed for job {job_id}: {e}")
        update_job_status(job, 'failed', str(e))
        _fail_processing_task(task, str(e))
        raise


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