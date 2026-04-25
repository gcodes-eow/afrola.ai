# backend/ai_engine/models.py

from django.db import models
from django.conf import settings
import uuid

class AIModel(models.Model):
    """Track AI models used for processing"""
    MODEL_TYPES = [
        ('asr', 'Speech Recognition'),
        ('translation', 'Translation'),
        ('tts', 'Text-to-Speech'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('training', 'Training'),
        ('deprecated', 'Deprecated'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)  # e.g., "whisper-large-v3", "nllb-200"
    model_type = models.CharField(max_length=20, choices=MODEL_TYPES)
    version = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Model metadata
    description = models.TextField(blank=True)
    accuracy_score = models.FloatField(null=True, blank=True, help_text="Model accuracy percentage")
    processing_time_avg = models.FloatField(null=True, blank=True, help_text="Average processing time in seconds")
    supported_languages = models.JSONField(default=list, help_text="List of supported language codes")
    model_size_mb = models.FloatField(null=True, blank=True)
    
    # File paths
    model_path = models.CharField(max_length=500, blank=True, help_text="Path to model files")
    config_path = models.CharField(max_length=500, blank=True, help_text="Path to model config")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['name', 'version']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} v{self.version} - {self.get_model_type_display()}"


class ProcessingTask(models.Model):
    """Track individual AI processing tasks within a job"""
    TASK_TYPES = [
        ('transcription', 'Transcription'),
        ('translation', 'Translation'),
        ('subtitle_generation', 'Subtitle Generation'),
        ('tts_synthesis', 'TTS Synthesis'),
        ('alignment', 'Alignment'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey('jobs.Job', on_delete=models.CASCADE, related_name='processing_tasks')
    task_type = models.CharField(max_length=50, choices=TASK_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Which AI model was used
    ai_model = models.ForeignKey(AIModel, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Task details
    input_data = models.JSONField(default=dict, help_text="Input parameters for the task")
    output_data = models.JSONField(default=dict, null=True, blank=True, help_text="Output results")
    
    # Performance tracking
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    processing_time = models.FloatField(null=True, blank=True, help_text="Processing time in seconds")
    
    # Error handling
    error_message = models.TextField(blank=True)
    retry_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.job.id} - {self.task_type} - {self.status}"


class LanguagePair(models.Model):
    """Supported language pairs for translation"""
    source_language = models.CharField(max_length=10)
    target_language = models.CharField(max_length=10)
    is_active = models.BooleanField(default=True)
    
    # Model performance for this pair
    bleu_score = models.FloatField(null=True, blank=True, help_text="Translation quality score")
    model = models.ForeignKey(AIModel, on_delete=models.SET_NULL, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['source_language', 'target_language']
    
    def __str__(self):
        return f"{self.source_language} → {self.target_language}"


class ProcessingQueue(models.Model):
    """Queue for tracking AI processing jobs with priority"""
    PRIORITY_CHOICES = [
        (1, 'Low'),
        (2, 'Normal'),
        (3, 'High'),
        (4, 'Urgent'),
    ]
    
    job = models.OneToOneField('jobs.Job', on_delete=models.CASCADE, related_name='queue_item')
    priority = models.IntegerField(choices=PRIORITY_CHOICES, default=2)
    position = models.IntegerField(null=True, blank=True, help_text="Position in queue")
    
    # Queue tracking
    queued_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Worker tracking
    worker_id = models.CharField(max_length=100, null=True, blank=True)
    celery_task_id = models.CharField(max_length=255, null=True, blank=True)
    
    class Meta:
        ordering = ['priority', 'queued_at']
    
    def __str__(self):
        return f"Job {self.job.id} - Priority {self.priority}"


class ProcessingLog(models.Model):
    """Log all AI processing events for debugging and analytics"""
    LOG_LEVELS = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('debug', 'Debug'),
    ]
    
    task = models.ForeignKey(ProcessingTask, on_delete=models.CASCADE, related_name='logs', null=True, blank=True)
    job = models.ForeignKey('jobs.Job', on_delete=models.CASCADE, related_name='logs', null=True, blank=True)
    
    level = models.CharField(max_length=10, choices=LOG_LEVELS, default='info')
    message = models.TextField()
    details = models.JSONField(default=dict, null=True, blank=True)
    
    # Source tracking
    source_file = models.CharField(max_length=255, blank=True)
    line_number = models.IntegerField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"[{self.level.upper()}] {self.message[:100]}"


class BatchProcessingJob(models.Model):
    """For processing multiple files as a batch"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='batch_jobs')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # Batch settings
    source_language = models.CharField(max_length=10)
    target_language = models.CharField(max_length=10)
    generate_subtitles = models.BooleanField(default=True)
    generate_audio = models.BooleanField(default=False)
    
    # Jobs in this batch
    jobs = models.ManyToManyField('jobs.Job', related_name='batches')
    
    # Status
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Progress
    total_jobs = models.IntegerField(default=0)
    completed_jobs = models.IntegerField(default=0)
    failed_jobs = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    @property
    def progress_percentage(self):
        if self.total_jobs == 0:
            return 0
        return (self.completed_jobs / self.total_jobs) * 100
    
    def __str__(self):
        return f"{self.name} - {self.status}"


class VoiceModel(models.Model):
    # Voice models for TTS
    name = models.CharField(max_length=100)
    language = models.CharField(max_length=10)
    gender = models.CharField(max_length=10)  # male/female/neutral
    accent = models.CharField(max_length=50, blank=True)
    is_cloned = models.BooleanField(default=False)
    voice_file = models.FileField(upload_to='voices/')
    sample_audio = models.FileField(upload_to='voice_samples/')
    
class DubbingJob(models.Model):
    """Extended job for dubbing"""
    job = models.OneToOneField(Job, on_delete=models.CASCADE)
    voice_model = models.ForeignKey(VoiceModel, null=True)
    output_video = models.FileField(upload_to='dubbed_videos/', null=True)
    output_audio = models.FileField(upload_to='dubbed_audio/', null=True)
    has_background_music = models.BooleanField(default=False)
    music_volume = models.FloatField(default=0.3)  # 0-1