# backend/utils/youtube_downloader.py

import os
from django.conf import settings


def download_youtube_audio(youtube_url, output_path):
    """Download audio from YouTube video"""
    try:
        from pytube import YouTube
        yt = YouTube(youtube_url)

        # Get audio stream
        audio_stream = yt.streams.filter(only_audio=True).first()
        if not audio_stream:
            return None, 'No audio stream available'

        # Download
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        audio_stream.download(output_path=os.path.dirname(output_path),
                              filename=os.path.basename(output_path))

        return output_path, None
    except Exception as e:
        return None, str(e)


def get_youtube_info(youtube_url):
    """Get YouTube video metadata"""
    try:
        from pytube import YouTube
        yt = YouTube(youtube_url)
        return {
            'title': yt.title,
            'duration': yt.length,
            'thumbnail_url': yt.thumbnail_url,
            'author': yt.author,
            'description': yt.description[:500],
        }
    except Exception:
        return None
