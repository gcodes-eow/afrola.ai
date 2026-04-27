# backend/config/logging.py

"""Centralized logging configuration for Afrola.ai."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / 'logs'
LOG_DIR.mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {module} {process:d} {thread:d} | {message}',
            'style': '{',
        },
        'simple': {
            'format': '[{levelname}] {asctime} | {message}',
            'style': '{',
        },
        'task': {
            'format': '[{levelname}] {asctime} TASK:{module} | {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(LOG_DIR / 'afrola.log'),
            'maxBytes': 10 * 1024 * 1024,  # 10 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'task_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(LOG_DIR / 'tasks.log'),
            'maxBytes': 10 * 1024 * 1024,  # 10 MB
            'backupCount': 5,
            'formatter': 'task',
        },
        'celery_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(LOG_DIR / 'celery.log'),
            'maxBytes': 10 * 1024 * 1024,  # 10 MB
            'backupCount': 3,
            'formatter': 'verbose',
        },
        'error_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(LOG_DIR / 'errors.log'),
            'maxBytes': 10 * 1024 * 1024,
            'backupCount': 3,
            'formatter': 'verbose',
            'level': 'ERROR',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['error_file', 'console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'celery': {
            'handlers': ['celery_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'celery.task': {
            'handlers': ['task_file', 'console'],
            'level': 'INFO',
            'formatter': 'task',
            'propagate': False,
        },
        'ai_engine': {
            'handlers': ['task_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'ai_engine.transcription': {
            'handlers': ['task_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'ai_engine.translation': {
            'handlers': ['task_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'ai_engine.tts': {
            'handlers': ['task_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'ai_engine.subtitle': {
            'handlers': ['task_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'ai_engine.pipeline': {
            'handlers': ['task_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'accounts': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
