# backend/dashboard/models.py

from django.db import models
from django.conf import settings
import uuid

class UserDashboard(models.Model):
    """User dashboard configuration and preferences"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='dashboard')
    
    # Layout preferences
    default_view = models.CharField(
        max_length=20,
        choices=[
            ('grid', 'Grid View'),
            ('list', 'List View'),
            ('table', 'Table View'),
        ],
        default='table'
    )
    
    items_per_page = models.IntegerField(default=10, choices=[(10, 10), (25, 25), (50, 50), (100, 100)])
    
    # Widget visibility
    show_stats_widget = models.BooleanField(default=True)
    show_recent_jobs_widget = models.BooleanField(default=True)
    show_usage_chart = models.BooleanField(default=True)
    show_notifications = models.BooleanField(default=True)
    
    # Theme preferences
    theme = models.CharField(
        max_length=20,
        choices=[
            ('light', 'Light'),
            ('dark', 'Dark'),
            ('system', 'System Default'),
        ],
        default='light'
    )
    
    # Notification preferences
    email_notifications = models.BooleanField(default=True)
    job_completion_notifications = models.BooleanField(default=True)
    job_failure_notifications = models.BooleanField(default=True)
    
    # Custom settings
    custom_settings = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.email}'s Dashboard"


class SavedItem(models.Model):
    """User saved/favorited jobs or results"""
    ITEM_TYPES = [
        ('job', 'Job'),
        ('transcript', 'Transcript'),
        ('translation', 'Translation'),
        ('subtitle', 'Subtitle File'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='saved_items')
    item_type = models.CharField(max_length=20, choices=ITEM_TYPES)
    item_id = models.UUIDField(help_text="ID of the referenced item")
    name = models.CharField(max_length=255)
    notes = models.TextField(blank=True)
    
    # Optional reference to job
    job = models.ForeignKey('jobs.Job', on_delete=models.CASCADE, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'item_type', 'item_id']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.name}"


class RecentActivity(models.Model):
    """Track user's recent activities for the dashboard"""
    ACTIVITY_TYPES = [
        ('job_created', 'Job Created'),
        ('job_completed', 'Job Completed'),
        ('job_failed', 'Job Failed'),
        ('file_uploaded', 'File Uploaded'),
        ('subscription_changed', 'Subscription Changed'),
        ('settings_updated', 'Settings Updated'),
        ('download', 'Download'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='recent_activities')
    activity_type = models.CharField(max_length=30, choices=ACTIVITY_TYPES)
    description = models.CharField(max_length=255)
    
    # Related objects
    job = models.ForeignKey('jobs.Job', on_delete=models.SET_NULL, null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Recent activities"
    
    def __str__(self):
        return f"{self.user.email} - {self.activity_type} - {self.created_at}"


class UserAnalytics(models.Model):
    """Store user analytics and usage statistics"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='analytics')
    
    # Usage statistics
    total_upload_time = models.FloatField(default=0, help_text="Total upload time in seconds")
    total_processing_time = models.FloatField(default=0, help_text="Total processing time in seconds")
    total_downloads = models.IntegerField(default=0)
    
    # Feature usage
    total_transcriptions = models.IntegerField(default=0)
    total_translations = models.IntegerField(default=0)
    total_subtitle_generations = models.IntegerField(default=0)
    total_audio_generations = models.IntegerField(default=0)
    
    # User engagement
    last_active = models.DateTimeField(auto_now=True)
    login_count = models.IntegerField(default=0)
    average_session_time = models.FloatField(default=0, help_text="Average session time in minutes")
    
    # File statistics
    total_files_uploaded = models.IntegerField(default=0)
    total_storage_used_mb = models.FloatField(default=0)
    average_file_size_mb = models.FloatField(default=0)
    
    # Language statistics
    most_used_source_language = models.CharField(max_length=10, null=True, blank=True)
    most_used_target_language = models.CharField(max_length=10, null=True, blank=True)
    
    # Export data
    last_export_date = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Analytics for {self.user.email}"


class DashboardWidget(models.Model):
    """Custom dashboard widgets for users"""
    WIDGET_TYPES = [
        ('stats', 'Statistics'),
        ('chart', 'Chart'),
        ('recent_jobs', 'Recent Jobs'),
        ('quota', 'Quota Usage'),
        ('tips', 'Tips & Tricks'),
        ('custom', 'Custom'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='widgets')
    widget_type = models.CharField(max_length=20, choices=WIDGET_TYPES)
    title = models.CharField(max_length=100)
    
    # Positioning
    column = models.IntegerField(default=0, help_text="Column position (0-2)")
    order = models.IntegerField(default=0, help_text="Order within column")
    
    # Widget settings
    is_visible = models.BooleanField(default=True)
    settings = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['column', 'order']
        unique_together = ['user', 'column', 'order']
    
    def __str__(self):
        return f"{self.user.email} - {self.title}"
