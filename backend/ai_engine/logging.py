"""Task-specific logging configuration for AI engine."""
import logging

# Create dedicated loggers for different task types
task_logger = logging.getLogger('celery.task')
transcription_logger = logging.getLogger('ai_engine.transcription')
translation_logger = logging.getLogger('ai_engine.translation')
tts_logger = logging.getLogger('ai_engine.tts')
subtitle_logger = logging.getLogger('ai_engine.subtitle')
pipeline_logger = logging.getLogger('ai_engine.pipeline')


def log_task_start(job_id, task_name):
    """Log task start with consistent format"""
    task_logger.info(f"[START] Job {job_id} - {task_name}")


def log_task_progress(job_id, task_name, progress, step):
    """Log task progress"""
    task_logger.info(f"[PROGRESS {progress}%] Job {job_id} - {task_name}: {step}")


def log_task_complete(job_id, task_name, duration):
    """Log task completion"""
    task_logger.info(f"[COMPLETE] Job {job_id} - {task_name} completed in {duration:.2f}s")


def log_task_failed(job_id, task_name, error):
    """Log task failure"""
    task_logger.error(f"[FAILED] Job {job_id} - {task_name}: {error}")


def log_task_retry(job_id, task_name, attempt, max_retries, error):
    """Log task retry"""
    task_logger.warning(f"[RETRY {attempt}/{max_retries}] Job {job_id} - {task_name}: {error}")
