# backend/utils/validators.py

import re
from django.conf import settings


def validate_file_type(filename, job_type):
    """Validate file extension against allowed types based on job type"""
    ext = filename.lower().split('.')[-1] if '.' in filename else ''

    if job_type in ['audio_to_text', 'audio_to_audio']:
        return ext in settings.ALLOWED_AUDIO_TYPES
    else:
        return ext in settings.ALLOWED_VIDEO_TYPES or ext in settings.ALLOWED_AUDIO_TYPES


def validate_file_size(file_size_bytes, subscription_tier):
    """Validate file size against tier limits"""
    limits = {
        'free': settings.FREE_MAX_UPLOAD_SIZE_MB,
        'pro': settings.PRO_MAX_UPLOAD_SIZE_MB,
        'enterprise': settings.ENTERPRISE_MAX_UPLOAD_SIZE_MB,
    }
    max_size_bytes = limits.get(subscription_tier, settings.FREE_MAX_UPLOAD_SIZE_MB) * 1024 * 1024
    return file_size_bytes <= max_size_bytes


def validate_youtube_url(url):
    """Validate YouTube URL format"""
    youtube_patterns = [
        r'^https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+',
        r'^https?://(?:www\.)?youtube\.com/embed/[\w-]+',
        r'^https?://youtu\.be/[\w-]+',
        r'^https?://(?:www\.)?youtube\.com/shorts/[\w-]+',
    ]
    return any(re.match(pattern, url) for pattern in youtube_patterns)


def validate_duration(duration_seconds, subscription_tier):
    """Validate media duration against tier limits"""
    limits = {
        'free': settings.FREE_MAX_DURATION_SECONDS,
        'pro': settings.PRO_MAX_DURATION_SECONDS,
        'enterprise': settings.ENTERPRISE_MAX_DURATION_SECONDS,
    }
    max_duration = limits.get(subscription_tier, settings.FREE_MAX_DURATION_SECONDS)
    return duration_seconds <= max_duration