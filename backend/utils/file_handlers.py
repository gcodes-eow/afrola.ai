# backend/utils/file_handlers.py

import os
import uuid
from django.conf import settings
from django.core.files.storage import default_storage
from django.utils import timezone


def save_uploaded_file(uploaded_file, user_id):
    """Save uploaded file with organized directory structure"""
    # Create directory path: uploads/user_id/YYYY/MM/DD/
    now = timezone.now()
    dir_path = os.path.join(
        'uploads',
        str(user_id),
        str(now.year),
        f'{now.month:02d}',
        f'{now.day:02d}'
    )
    full_dir = os.path.join(settings.MEDIA_ROOT, dir_path)
    os.makedirs(full_dir, exist_ok=True)

    # Generate unique filename
    ext = uploaded_file.name.split('.')[-1] if '.' in uploaded_file.name else ''
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    file_path = os.path.join(dir_path, unique_name)

    # Save file
    saved_path = default_storage.save(file_path, uploaded_file)
    return saved_path


def create_job_directory(job_id):
    """Create output directory for a job"""
    dir_path = os.path.join(settings.MEDIA_ROOT, 'outputs', str(job_id))
    os.makedirs(dir_path, exist_ok=True)
    return dir_path


def get_file_size(file_path):
    """Get file size in bytes"""
    full_path = os.path.join(settings.MEDIA_ROOT, file_path)
    if os.path.exists(full_path):
        return os.path.getsize(full_path)
    return 0


def generate_job_filename(job_id, output_type, extension):
    """Generate consistent output filenames"""
    return f"{job_id}_{output_type}.{extension}"