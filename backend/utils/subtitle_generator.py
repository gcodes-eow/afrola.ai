# backend/utils/subtitle_generator.py

import os
from django.conf import settings


def generate_srt(segments):
    """Generate SRT subtitle content from transcript segments"""
    srt_content = ""
    for i, segment in enumerate(segments, 1):
        start_time = _format_srt_time(segment.get('start', 0))
        end_time = _format_srt_time(segment.get('end', 0))
        text = segment.get('text', '')
        srt_content += f"{i}\n{start_time} --> {end_time}\n{text}\n\n"
    return srt_content


def generate_vtt(segments):
    """Generate WebVTT subtitle content from transcript segments"""
    vtt_content = "WEBVTT\n\n"
    for i, segment in enumerate(segments, 1):
        start_time = _format_vtt_time(segment.get('start', 0))
        end_time = _format_vtt_time(segment.get('end', 0))
        text = segment.get('text', '')
        vtt_content += f"{start_time} --> {end_time}\n{text}\n\n"
    return vtt_content


def save_subtitle_file(job, content, format_type='srt'):
    """Save subtitle content to file"""
    from utils.file_handlers import create_job_directory
    output_dir = create_job_directory(str(job.id))
    filename = f"subtitles.{format_type}"
    file_path = os.path.join(output_dir, filename)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    return os.path.relpath(file_path, settings.MEDIA_ROOT)


def _format_srt_time(seconds):
    """Format time for SRT: HH:MM:SS,mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def _format_vtt_time(seconds):
    """Format time for WebVTT: HH:MM:SS.mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"
