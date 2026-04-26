# backend/utils/ffmpeg_utils.py

import subprocess
import json
import os
from django.conf import settings


def get_media_duration(file_path):
    """Extract duration of audio/video file using ffprobe"""
    try:
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            file_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return float(data.get('format', {}).get('duration', 0))
    except (subprocess.TimeoutExpired, json.JSONDecodeError, ValueError, FileNotFoundError):
        pass
    return None


def extract_audio_from_video(video_path, audio_output_path, format='mp3'):
    """Extract audio track from video file using ffmpeg"""
    try:
        os.makedirs(os.path.dirname(audio_output_path), exist_ok=True)
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-vn',  # No video
            '-acodec', 'libmp3lame' if format == 'mp3' else 'pcm_s16le',
            '-ar', '16000',  # 16kHz for ASR
            '-ac', '1',  # Mono
            '-y',  # Overwrite
            audio_output_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def get_media_info(file_path):
    """Get detailed media information"""
    try:
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            file_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return json.loads(result.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
        pass
    return None