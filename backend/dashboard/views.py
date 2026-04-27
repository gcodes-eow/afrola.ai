# backend/dashboard/views.py
import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from .forms import MediaUploadForm
from jobs.models import Job
from jobs.utils import create_job_record
from utils.validators import validate_file_type, validate_file_size, validate_youtube_url
from utils.file_handlers import save_uploaded_file
from utils.ffmpeg_utils import get_media_duration


@login_required
def index(request):
    """Dashboard home page"""
    recent_jobs = request.user.jobs.all().order_by('-created_at')[:5]

    context = {
        'recent_jobs': recent_jobs,
        'total_jobs': request.user.jobs.count(),
        'completed_jobs': request.user.jobs.filter(status='completed').count(),
        'processing_jobs': request.user.jobs.filter(status__in=['pending', 'queued', 'processing']).count(),
    }
    return render(request, 'dashboard/index.html', context)


@login_required
def upload_media(request):
    """Handle media upload, text input, and YouTube URL submission"""
    if request.method == 'POST':
        form = MediaUploadForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            try:
                input_type = form.cleaned_data['input_type']
                job_type = form.cleaned_data['job_type']
                source_language = form.cleaned_data['source_language']
                target_language = form.cleaned_data['target_language']

                source_file = None
                youtube_url = None
                source_text = None
                duration = None
                file_size = None

                if input_type == 'text':
                    source_text = form.cleaned_data['source_text']

                    # Enforce character limits by tier
                    text_limits = {'free': 1000, 'pro': 50000, 'business': None}
                    char_limit = text_limits.get(request.user.subscription_tier, 1000)

                    if char_limit and len(source_text) > char_limit:
                        messages.error(request, f'Text too long. Maximum {char_limit:,} characters for your plan. Upgrade for more.')
                        return render(request, 'dashboard/upload.html', {'form': form})

                elif input_type == 'file':
                    uploaded_file = request.FILES['source_file']

                    if not validate_file_type(uploaded_file.name, job_type):
                        messages.error(request, 'Unsupported file format. Please use supported formats.')
                        return render(request, 'dashboard/upload.html', {'form': form})

                    if not validate_file_size(uploaded_file.size, request.user.subscription_tier):
                        max_size = settings.FREE_MAX_UPLOAD_SIZE_MB
                        if request.user.subscription_tier == 'pro':
                            max_size = settings.PRO_MAX_UPLOAD_SIZE_MB
                        elif request.user.subscription_tier == 'business':
                            max_size = settings.BUSINESS_MAX_UPLOAD_SIZE_MB
                        messages.error(request, f'File too large. Maximum {max_size}MB for your plan. Upgrade for larger files.')
                        return render(request, 'dashboard/upload.html', {'form': form})

                    source_file = save_uploaded_file(uploaded_file, request.user.id)
                    file_size = uploaded_file.size

                    file_path = os.path.join(settings.MEDIA_ROOT, source_file.name)
                    duration = get_media_duration(file_path)

                    if duration:
                        max_duration = settings.FREE_MAX_DURATION_SECONDS
                        if request.user.subscription_tier == 'pro':
                            max_duration = settings.PRO_MAX_DURATION_SECONDS
                        elif request.user.subscription_tier == 'business':
                            max_duration = settings.BUSINESS_MAX_DURATION_SECONDS

                        if duration > max_duration:
                            messages.error(request, f'File too long ({int(duration)}s). Maximum {max_duration}s for your plan. Upgrade for longer files.')
                            return render(request, 'dashboard/upload.html', {'form': form})

                elif input_type == 'youtube':
                    youtube_url = form.cleaned_data['youtube_url']

                    if not validate_youtube_url(youtube_url):
                        messages.error(request, 'Invalid YouTube URL. Please enter a valid YouTube video link.')
                        return render(request, 'dashboard/upload.html', {'form': form})

                output_types = form.cleaned_data.get('output_types', [])
                if not output_types:
                    output_types = ['transcript', 'translation']

                job = create_job_record(
                    user=request.user,
                    job_type=job_type,
                    source_language=source_language,
                    target_language=target_language,
                    source_file=source_file,
                    youtube_url=youtube_url,
                    source_text=source_text,
                    output_types=output_types,
                    duration=duration,
                    file_size=file_size,
                    voice_model=form.cleaned_data.get('voice_model'),
                    add_background_music=form.cleaned_data.get('add_background_music', False),
                    background_music_file=form.cleaned_data.get('background_music_file'),
                    music_volume=form.cleaned_data.get('music_volume', 0.3),
                    preserve_timestamps=form.cleaned_data.get('preserve_timestamps', True),
                )

                messages.success(request, 'Job created successfully! Processing will begin shortly.')
                return redirect('dashboard:job_detail', job_id=job.id)

            except Exception as e:
                messages.error(request, f'Error creating job: {str(e)}')
                return render(request, 'dashboard/upload.html', {'form': form})
    else:
        form = MediaUploadForm(user=request.user)

    context = {
        'form': form,
        'supported_audio_types': settings.ALLOWED_AUDIO_TYPES,
        'supported_video_types': settings.ALLOWED_VIDEO_TYPES,
        'max_file_size_mb': settings.FREE_MAX_UPLOAD_SIZE_MB,
        'max_duration_seconds': settings.FREE_MAX_DURATION_SECONDS,
    }
    return render(request, 'dashboard/upload.html', context)


@login_required
def job_detail(request, job_id):
    """View job details and results"""
    job = get_object_or_404(Job, id=job_id, user=request.user)

    context = {
        'job': job,
        'outputs': job.get_output_files(),
    }
    return render(request, 'dashboard/job_detail.html', context)


@login_required
def download_result(request, job_id, output_type):
    """Download a specific output file"""
    job = get_object_or_404(Job, id=job_id, user=request.user)

    if not job.can_download(request.user):
        messages.error(request, 'You cannot download this job yet.')
        return redirect('dashboard:job_detail', job_id=job.id)

    output_files = job.get_output_files()
    if output_type in output_files:
        return redirect(output_files[output_type])

    messages.error(request, 'File not found.')
    return redirect('dashboard:job_detail', job_id=job.id)