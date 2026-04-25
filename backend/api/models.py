# backend/api/models.py
from django.db import models
from django.conf import settings
import uuid

class APIKey(models.Model):
    """API keys for programmatic access"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='api_keys')
    
    # Key details
    name = models.CharField(max_length=100, help_text="Name to identify the key")
    key = models.CharField(max_length=255, unique=True)
    key_prefix = models.CharField(max_length=10, help_text="First few characters for identification")
    
    # Permissions
    permissions = models.JSONField(default=list, help_text="List of allowed permissions/endpoints")
    
    # Rate limiting
    rate_limit_per_minute = models.IntegerField(default=60)
    rate_limit_per_day = models.IntegerField(default=1000)
    
    # Usage tracking
    last_used_at = models.DateTimeField(null=True, blank=True)
    total_requests = models.IntegerField(default=0)
    
    # Status
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "API Key"
        verbose_name_plural = "API Keys"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.name} ({self.key_prefix}...)"
    
    @property
    def is_expired(self):
        if self.expires_at:
            from django.utils import timezone
            return self.expires_at <= timezone.now()
        return False


class APIRequestLog(models.Model):
    """Log all API requests for monitoring and analytics"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    api_key = models.ForeignKey(APIKey, on_delete=models.SET_NULL, null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Request details
    method = models.CharField(max_length=10)
    path = models.CharField(max_length=500)
    query_params = models.JSONField(default=dict, blank=True)
    
    # Response details
    status_code = models.IntegerField()
    response_time_ms = models.IntegerField(help_text="Response time in milliseconds")
    
    # Rate limiting
    rate_limit_remaining = models.IntegerField(null=True, blank=True)
    
    # Client info
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Error tracking
    error_message = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['api_key', 'created_at']),
            models.Index(fields=['status_code']),
        ]
    
    def __str__(self):
        return f"{self.method} {self.path} - {self.status_code} - {self.created_at}"


class WebhookEndpoint(models.Model):
    """Webhook endpoints for real-time notifications"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='webhooks')
    
    # Endpoint details
    name = models.CharField(max_length=100)
    url = models.URLField(max_length=500)
    secret = models.CharField(max_length=255, help_text="Secret for signing webhooks")
    
    # Events to send
    events = models.JSONField(default=list, help_text="List of event types to send")
    
    # Status
    is_active = models.BooleanField(default=True)
    last_triggered_at = models.DateTimeField(null=True, blank=True)
    failure_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.name}"


class WebhookDelivery(models.Model):
    """Log of webhook delivery attempts"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('retry', 'Retry'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    webhook = models.ForeignKey(WebhookEndpoint, on_delete=models.CASCADE, related_name='deliveries')
    
    # Event details
    event_type = models.CharField(max_length=100)
    payload = models.JSONField()
    
    # Delivery details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    response_status_code = models.IntegerField(null=True, blank=True)
    response_body = models.TextField(blank=True)
    
    # Retry info
    attempt_count = models.IntegerField(default=0)
    next_retry_at = models.DateTimeField(null=True, blank=True)
    
    # Timing
    delivered_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Webhook deliveries"
    
    def __str__(self):
        return f"{self.webhook.name} - {self.event_type} - {self.status}"


class RateLimitRule(models.Model):
    """Rate limiting rules for API endpoints"""
    TIME_WINDOWS = [
        ('second', 'Per Second'),
        ('minute', 'Per Minute'),
        ('hour', 'Per Hour'),
        ('day', 'Per Day'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    endpoint_pattern = models.CharField(max_length=500, help_text="Regex pattern for endpoint paths")
    method = models.CharField(max_length=10, null=True, blank=True, help_text="HTTP method (GET, POST, etc.)")
    
    # Rate limits
    requests = models.IntegerField(help_text="Number of requests allowed")
    time_window = models.CharField(max_length=10, choices=TIME_WINDOWS, default='minute')
    
    # Applicability
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(default=0, help_text="Higher priority rules are checked first")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-priority', 'requests']
    
    def __str__(self):
        return f"{self.name} - {self.requests}/{self.time_window}"


class APIAccessLog(models.Model):
    """Detailed API access log for compliance and debugging"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request_log = models.OneToOneField(APIRequestLog, on_delete=models.CASCADE, related_name='access_log')
    
    # Request headers (sensitive data masked)
    request_headers = models.JSONField(default=dict)
    response_headers = models.JSONField(default=dict)
    
    # Request/response size
    request_size_bytes = models.IntegerField(null=True, blank=True)
    response_size_bytes = models.IntegerField(null=True, blank=True)
    
    # Performance metrics
    db_query_count = models.IntegerField(default=0)
    db_query_time_ms = models.FloatField(default=0)
    
    # Rate limit info
    rate_limit_rule = models.ForeignKey(RateLimitRule, on_delete=models.SET_NULL, null=True)
    rate_limit_reset_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Access Log - {self.request_log.created_at}"


class APIUsageSummary(models.Model):
    """Daily/monthly API usage summary for analytics"""
    PERIOD_TYPES = [
        ('day', 'Daily'),
        ('week', 'Weekly'),
        ('month', 'Monthly'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='api_usage_summaries')
    period_type = models.CharField(max_length=10, choices=PERIOD_TYPES)
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    
    # Usage counts
    total_requests = models.IntegerField(default=0)
    successful_requests = models.IntegerField(default=0)
    failed_requests = models.IntegerField(default=0)
    
    # Performance
    avg_response_time_ms = models.FloatField(default=0)
    total_response_time_ms = models.FloatField(default=0)
    
    # Resources
    total_minutes_processed = models.FloatField(default=0)
    total_bytes_transferred = models.BigIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'period_type', 'period_start']
        ordering = ['-period_start']
    
    def __str__(self):
        return f"{self.user.email} - {self.period_type} - {self.period_start.date()}"
