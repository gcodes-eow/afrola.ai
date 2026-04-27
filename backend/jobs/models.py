# backend/jobs/models.py

from django.db import models
from django.conf import settings
import uuid

class Job(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('queued', 'Queued'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Extended job types for full dubbing capabilities
    TYPE_CHOICES = [
        # Text/Subtitle outputs
        ('text_to_text', 'Text → Text'),
        ('audio_to_text', 'Audio → Text'),
        ('video_to_text', 'Video → Text'),
        # Audio dubbing
        ('audio_to_audio', 'Audio → Audio Dubbing'),
        ('video_to_audio', 'Video → Audio Dubbing'),
        # Video dubbing
        ('video_to_video', 'Video → Video Dubbing'),
        ('youtube_to_video', 'YouTube → Dubbed Video'),
    ]
    
    # Output types supported by this job
    OUTPUT_TYPE_CHOICES = [
        ('transcript', 'Transcript'),
        ('translation', 'Translation'),
        ('subtitles', 'Subtitles'),
        ('dubbed_audio', 'Dubbed Audio'),
        ('dubbed_video', 'Dubbed Video'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='jobs')
    title = models.CharField(max_length=255, blank=True)
    job_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    output_types = models.JSONField(default=list, help_text="List of output types requested")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.IntegerField(default=0, help_text="Higher = higher priority")
    
    # Input
    source_file = models.FileField(upload_to='uploads/%Y/%m/%d/', null=True, blank=True)
    youtube_url = models.URLField(null=True, blank=True)
    source_language = models.CharField(max_length=10, default='lg')
    target_language = models.CharField(max_length=10, default='en')
    
    # Output - Text/Subtitle
    transcript = models.TextField(blank=True)
    translation = models.TextField(blank=True)
    subtitle_file = models.FileField(upload_to='subtitles/%Y/%m/%d/', null=True, blank=True)
    
    # Output - Audio/Video Dubbing
    dubbed_audio = models.FileField(upload_to='dubbed_audio/%Y/%m/%d/', null=True, blank=True)
    dubbed_video = models.FileField(upload_to='dubbed_video/%Y/%m/%d/', null=True, blank=True)
    
    # Dubbing Options
    voice_model = models.CharField(max_length=100, null=True, blank=True, 
                                   help_text="Voice model to use for TTS")
    add_background_music = models.BooleanField(default=False)
    background_music_file = models.FileField(upload_to='background_music/', null=True, blank=True)
    music_volume = models.FloatField(default=0.3, help_text="Background music volume (0-1)")
    preserve_timestamps = models.BooleanField(default=True, 
                                             help_text="Preserve original timing in dubbed output")
    
    # Metadata
    duration = models.FloatField(null=True, blank=True, help_text="Duration in seconds")
    file_size = models.BigIntegerField(null=True, blank=True, help_text="File size in bytes")
    processing_time = models.FloatField(null=True, blank=True, help_text="Processing time in seconds")
    error_message = models.TextField(blank=True)
    retry_count = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    queued_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['created_at']),
            models.Index(fields=['job_type']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.get_job_type_display()} - {self.status}"
    
    @property
    def progress(self):
        """Calculate job progress percentage"""
        if self.status == 'completed':
            return 100
        elif self.status == 'processing':
            # Could be enhanced with task-specific progress
            return 50
        elif self.status == 'queued':
            return 25
        return 0
    
    @property
    def has_dubbing(self):
        """Check if this job requires dubbing"""
        dubbing_types = ['audio_to_audio', 'video_to_audio', 'video_to_video', 'youtube_to_video']
        return self.job_type in dubbing_types
    
    @property
    def requires_video_output(self):
        """Check if output should be video"""
        return self.job_type in ['video_to_video', 'youtube_to_video']
    
    @property
    def requires_audio_output(self):
        """Check if output should be audio"""
        return self.job_type in ['audio_to_audio', 'video_to_audio']
    
    @property
    def requires_transcription(self):
        """Check if transcription is needed"""
        return self.job_type in [
            'audio_to_text', 'video_to_text', 
            'audio_to_audio', 'video_to_audio', 
            'video_to_video', 'youtube_to_video'
        ]
    
    @property
    def requires_translation(self):
        """Check if translation is needed (different languages)"""
        return self.source_language != self.target_language
    
    def can_download(self, user):
        """Check if user can download results"""
        return user == self.user and self.status == 'completed'
    
    def get_output_files(self):
        """Return dictionary of available output files"""
        outputs = {}
        if self.transcript:
            outputs['transcript'] = self.transcript
        if self.translation:
            outputs['translation'] = self.translation
        if self.subtitle_file:
            outputs['subtitles'] = self.subtitle_file.url
        if self.dubbed_audio:
            outputs['dubbed_audio'] = self.dubbed_audio.url
        if self.dubbed_video:
            outputs['dubbed_video'] = self.dubbed_video.url
        return outputs
    
    def save(self, *args, **kwargs):
        # Auto-calculate duration from file if not set
        if self.source_file and not self.duration and self.source_file.name:
            # Will be set during processing
            pass
        
        # Set default title if not provided
        if not self.title and self.source_file:
            self.title = self.source_file.name.split('/')[-1]
        elif not self.title and self.youtube_url:
            self.title = "YouTube Video"
        
        super().save(*args, **kwargs)

class FailedTask(models.Model):
    """Store failed tasks for manual review and retry"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task_id = models.CharField(max_length=255, unique=True, help_text="Celery task ID")
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='failed_tasks')
    task_name = models.CharField(max_length=255, help_text="Name of the Celery task")
    error = models.TextField(help_text="Error message")
    traceback = models.TextField(blank=True, help_text="Full traceback")
    retry_count = models.IntegerField(default=0)
    resolved = models.BooleanField(default=False, help_text="Whether the issue has been resolved")
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_tasks'
    )
    resolution_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Failed Task"
        verbose_name_plural = "Failed Tasks"

    def __str__(self):
        return f"Failed: {self.task_name} - Job {self.job.id}"

    def resolve(self, user, notes=''):
        """Mark this failed task as resolved"""
        self.resolved = True
        self.resolved_by = user
        self.resolution_notes = notes
        self.save()