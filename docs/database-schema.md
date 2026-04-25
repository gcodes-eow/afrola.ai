docs/database-schema.md

# Database Schema — Afrola.ai (Django ORM)

## Purpose
Define all database models using Django ORM, relationships, and indexes for the complete media localization platform including transcription, translation, dubbing, payments, and API access.

## Model Overview

### Core Models
accounts.User → Extended user model with subscriptions
jobs.Job → Processing jobs (all types)
ai_engine.AIModel → Registered AI models
ai_engine.ProcessingTask → Individual AI pipeline tasks
ai_engine.LanguagePair → Supported language translations
ai_engine.BatchProcessingJob → Batch job processing
pricing.PricingPlan → Subscription tiers
payments.UserSubscription → User subscriptions
payments.PaymentTransaction → Payment records
payments.Invoice → Billing invoices
payments.PromoCode → Discount codes
dashboard.UserDashboard → User preferences
dashboard.SavedItem → Saved/favorited content
dashboard.RecentActivity → User activity log
dashboard.UserAnalytics → Usage statistics
api.APIKey → API access keys
api.WebhookEndpoint → Webhook configurations
api.RateLimitRule → API rate limiting rules

## Model Definitions

### 1. User Model (accounts.User)


class User(AbstractUser):
    """Extended user model with subscription and usage tracking"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    
    # Subscription
    subscription_tier = models.CharField(
        max_length=20,
        choices=[('free', 'Free'), ('pro', 'Pro'), ('enterprise', 'Enterprise')],
        default='free'
    )
    subscription_end_date = models.DateTimeField(null=True, blank=True)
    stripe_customer_id = models.CharField(max_length=255, null=True, blank=True)
    
    # Usage tracking
    monthly_processing_seconds = models.BigIntegerField(default=0)
    monthly_jobs_count = models.IntegerField(default=0)
    last_reset_date = models.DateField(auto_now_add=True)
    
    # Verification
    email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=255, null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'full_name']
    
    class Meta:
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['subscription_tier']),
            models.Index(fields=['created_at']),
        ]

2. Job Model (jobs.Job)

class Job(models.Model):
    """Complete job management for all processing types"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('queued', 'Queued'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    TYPE_CHOICES = [
        ('audio_to_text', 'Audio → Text'),
        ('video_to_text', 'Video → Text'),
        ('audio_to_audio', 'Audio → Audio Dubbing'),
        ('video_to_audio', 'Video → Audio Dubbing'),
        ('video_to_video', 'Video → Video Dubbing'),
        ('youtube_to_video', 'YouTube → Dubbed Video'),
    ]
    
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
    priority = models.IntegerField(default=0)
    
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
    voice_model = models.CharField(max_length=100, null=True, blank=True)
    add_background_music = models.BooleanField(default=False)
    background_music_file = models.FileField(upload_to='background_music/', null=True, blank=True)
    music_volume = models.FloatField(default=0.3)
    preserve_timestamps = models.BooleanField(default=True)
    
    # Metadata
    duration = models.FloatField(null=True, blank=True, help_text="Duration in seconds")
    file_size = models.BigIntegerField(null=True, blank=True)
    processing_time = models.FloatField(null=True, blank=True)
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

3. AI Engine Models (ai_engine)

class AIModel(models.Model):
    """Track AI models used for processing"""
    
    MODEL_TYPES = [('asr', 'Speech Recognition'), ('translation', 'Translation'), ('tts', 'Text-to-Speech')]
    STATUS_CHOICES = [('active', 'Active'), ('inactive', 'Inactive'), ('training', 'Training'), ('deprecated', 'Deprecated')]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    model_type = models.CharField(max_length=20, choices=MODEL_TYPES)
    version = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    description = models.TextField(blank=True)
    accuracy_score = models.FloatField(null=True, blank=True)
    processing_time_avg = models.FloatField(null=True, blank=True)
    supported_languages = models.JSONField(default=list)
    model_size_mb = models.FloatField(null=True, blank=True)
    model_path = models.CharField(max_length=500, blank=True)
    
    class Meta:
        unique_together = ['name', 'version']


class LanguagePair(models.Model):
    """Supported language pairs for translation"""
    
    source_language = models.CharField(max_length=10)
    target_language = models.CharField(max_length=10)
    is_active = models.BooleanField(default=True)
    bleu_score = models.FloatField(null=True, blank=True)
    model = models.ForeignKey(AIModel, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        unique_together = ['source_language', 'target_language']


class ProcessingTask(models.Model):
    """Track individual AI processing tasks within a job"""
    
    TASK_TYPES = [('transcription', 'Transcription'), ('translation', 'Translation'), 
                  ('subtitle_generation', 'Subtitle Generation'), ('tts_synthesis', 'TTS Synthesis')]
    STATUS_CHOICES = [('pending', 'Pending'), ('processing', 'Processing'), ('completed', 'Completed'), ('failed', 'Failed')]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey('jobs.Job', on_delete=models.CASCADE, related_name='processing_tasks')
    task_type = models.CharField(max_length=50, choices=TASK_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    ai_model = models.ForeignKey(AIModel, on_delete=models.SET_NULL, null=True)
    input_data = models.JSONField(default=dict)
    output_data = models.JSONField(default=dict, null=True, blank=True)
    processing_time = models.FloatField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    retry_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

4. Pricing & Payment Models

# pricing/models.py
class PricingPlan(models.Model):
    """Available subscription plans"""
    
    TIER_CHOICES = [('free', 'Free'), ('pro', 'Pro'), ('enterprise', 'Enterprise')]
    BILLING_PERIODS = [('monthly', 'Monthly'), ('yearly', 'Yearly')]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50)
    tier = models.CharField(max_length=20, choices=TIER_CHOICES)
    billing_period = models.CharField(max_length=20, choices=BILLING_PERIODS, default='monthly')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_minutes_per_month = models.IntegerField(default=60)
    max_file_size_mb = models.IntegerField(default=100)
    max_jobs_per_month = models.IntegerField(default=10)
    concurrent_jobs = models.IntegerField(default=1)
    features = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    stripe_price_id = models.CharField(max_length=255, null=True, blank=True)


# payments/models.py
class UserSubscription(models.Model):
    """User's current subscription"""
    
    STATUS_CHOICES = [('active', 'Active'), ('trialing', 'Trialing'), ('past_due', 'Past Due'), ('canceled', 'Canceled')]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subscription')
    plan = models.ForeignKey(PricingPlan, on_delete=models.SET_NULL, null=True)
    stripe_subscription_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    current_period_start = models.DateTimeField()
    current_period_end = models.DateTimeField()
    cancel_at_period_end = models.BooleanField(default=False)
    minutes_used_this_period = models.IntegerField(default=0)
    jobs_used_this_period = models.IntegerField(default=0)


class PaymentTransaction(models.Model):
    """Track all payment transactions"""
    
    STATUS_CHOICES = [('pending', 'Pending'), ('succeeded', 'Succeeded'), ('failed', 'Failed'), ('refunded', 'Refunded')]
    PAYMENT_METHODS = [('card', 'Credit Card'), ('mobile_money', 'Mobile Money'), ('bank_transfer', 'Bank Transfer')]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transactions')
    subscription = models.ForeignKey(UserSubscription, on_delete=models.SET_NULL, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    stripe_payment_intent_id = models.CharField(max_length=255, null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)

5. Dashboard Models (dashboard)

class UserDashboard(models.Model):
    """User dashboard configuration and preferences"""
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='dashboard')
    default_view = models.CharField(max_length=20, choices=[('grid', 'Grid'), ('list', 'List'), ('table', 'Table')], default='table')
    items_per_page = models.IntegerField(default=10)
    show_stats_widget = models.BooleanField(default=True)
    show_recent_jobs_widget = models.BooleanField(default=True)
    theme = models.CharField(max_length=20, choices=[('light', 'Light'), ('dark', 'Dark')], default='light')
    email_notifications = models.BooleanField(default=True)


class SavedItem(models.Model):
    """User saved/favorited jobs or results"""
    
    ITEM_TYPES = [('job', 'Job'), ('transcript', 'Transcript'), ('translation', 'Translation'), ('subtitle', 'Subtitle')]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='saved_items')
    item_type = models.CharField(max_length=20, choices=ITEM_TYPES)
    item_id = models.UUIDField()
    name = models.CharField(max_length=255)
    job = models.ForeignKey('jobs.Job', on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'item_type', 'item_id']


class RecentActivity(models.Model):
    """Track user's recent activities"""
    
    ACTIVITY_TYPES = [('job_created', 'Job Created'), ('job_completed', 'Job Completed'), ('job_failed', 'Job Failed'), 
                      ('file_uploaded', 'File Uploaded'), ('subscription_changed', 'Subscription Changed')]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='recent_activities')
    activity_type = models.CharField(max_length=30, choices=ACTIVITY_TYPES)
    description = models.CharField(max_length=255)
    job = models.ForeignKey('jobs.Job', on_delete=models.SET_NULL, null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
6. API Models (api)
python
class APIKey(models.Model):
    """API keys for programmatic access"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='api_keys')
    name = models.CharField(max_length=100)
    key = models.CharField(max_length=255, unique=True)
    key_prefix = models.CharField(max_length=10)
    permissions = models.JSONField(default=list)
    rate_limit_per_minute = models.IntegerField(default=60)
    rate_limit_per_day = models.IntegerField(default=1000)
    last_used_at = models.DateTimeField(null=True, blank=True)
    total_requests = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class WebhookEndpoint(models.Model):
    """Webhook endpoints for real-time notifications"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='webhooks')
    name = models.CharField(max_length=100)
    url = models.URLField(max_length=500)
    secret = models.CharField(max_length=255)
    events = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    failure_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)


class RateLimitRule(models.Model):
    """Rate limiting rules for API endpoints"""
    
    TIME_WINDOWS = [('second', 'Per Second'), ('minute', 'Per Minute'), ('hour', 'Per Hour'), ('day', 'Per Day')]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    endpoint_pattern = models.CharField(max_length=500)
    method = models.CharField(max_length=10, null=True, blank=True)
    requests = models.IntegerField()
    time_window = models.CharField(max_length=10, choices=TIME_WINDOWS, default='minute')
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(default=0)
Relationships Diagram

┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│     User        │     │      Job        │     │  ProcessingTask │
│─────────────────│     │─────────────────│     │─────────────────│
│ id (PK)         │────<│ user_id (FK)    │     │ id (PK)         │
│ email           │     │ id (PK)         │────<│ job_id (FK)     │
│ subscription_tier│     │ job_type        │     │ task_type       │
│ monthly_*       │     │ source_language │     │ status          │
└─────────────────┘     │ target_language │     └─────────────────┘
         │              │ status          │              │
         │              │ transcript      │              │
         │              │ dubbed_audio    │              │
         │              └─────────────────┘              │
         │                      │                       │
         ▼                      ▼                       ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ UserSubscription│     │   PricingPlan   │     │    AIModel      │
│─────────────────│     │─────────────────│     │─────────────────│
│ user_id (FK)    │────<│ id (PK)         │     │ id (PK)         │
│ plan_id (FK)    │>────│ name            │────<│ model_type      │
│ stripe_sub_id   │     │ tier            │     │ supported_langs │
└─────────────────┘     │ price           │     └─────────────────┘
                        └─────────────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ PaymentTransaction│    │     APIKey      │     │   SavedItem     │
│─────────────────│     │─────────────────│     │─────────────────│
│ user_id (FK)    │     │ user_id (FK)    │     │ user_id (FK)    │
│ subscription_id │     │ key             │     │ job_id (FK)     │
│ amount          │     │ rate_limit_*    │     │ item_type       │
└─────────────────┘     └─────────────────┘     └─────────────────┘

Indexes Required

Table	Index	Type	Purpose
Job	(user_id, status, created_at)	Composite	Dashboard job listing
Job	(status, priority)	Composite	Queue processing order
Job	(job_type, status)	Composite	Filter by type
User	(email)	Unique	Authentication
User	(subscription_tier, created_at)	Composite	Analytics
UserSubscription	(user_id, status)	Composite	Subscription status check
UserSubscription	(stripe_subscription_id)	Unique	Webhook matching
APIKey	(user_id, is_active)	Composite	API authentication
APIKey	(key)	Unique	API key lookup
ProcessingTask	(job_id, status)	Composite	Task status tracking
PaymentTransaction	(user_id, created_at)	Composite	Payment history
PaymentTransaction	(stripe_payment_intent_id)	Unique	Webhook matching
Model Relationships Summary
Source Model	Target Model	Relationship	Cascade
User	Job	One-to-Many	CASCADE
User	UserSubscription	One-to-One	CASCADE
User	APIKey	One-to-Many	CASCADE
User	SavedItem	One-to-Many	CASCADE
User	PaymentTransaction	One-to-Many	CASCADE
Job	ProcessingTask	One-to-Many	CASCADE
Job	SavedItem	Many-to-One	SET_NULL
UserSubscription	PricingPlan	Many-to-One	SET_NULL
PaymentTransaction	UserSubscription	Many-to-One	SET_NULL
ProcessingTask	AIModel	Many-to-One	SET_NULL
Required Files

backend/accounts/models.py             # ✅ Custom User model
backend/jobs/models.py                 # ✅ Job model with dubbing fields
backend/ai_engine/models.py            # ✅ AI models, tasks, language pairs
backend/pricing/models.py              # ✅ PricingPlan model
backend/payments/models.py             # ✅ Subscription, transactions, invoices
backend/dashboard/models.py            # ✅ Dashboard, saved items, activities
backend/api/models.py                  # ✅ APIKey, Webhook, RateLimitRule
Migrations Status

# Current migrations applied:
accounts: 0001_initial ✓
jobs: 0001_initial ✓
ai_engine: 0001_initial ✓
pricing: 0001_initial ✓
payments: 0001_initial ✓
api: 0001_initial ✓
dashboard: 0001_initial ✓
Verification Checklist
All models have __str__ method for admin display

Foreign keys have on_delete properly set (CASCADE/PROTECT/SET_NULL)

Indexes defined for frequent query patterns

Unique constraints properly set (email, API keys, Stripe IDs)

JSONField used where dynamic data is needed

FileField has upload_to path defined with date formatting

DecimalField has proper max_digits and decimal_places

UUID fields are used for public-facing IDs (security)

Model tests cover relationships and constraints

Migrations are version controlled

No circular dependencies between models

Related Documentation
docs/user-auth-flow.md - User model usage

docs/file-upload-flow.md - Job model for uploads

docs/celery-queue-flow.md - Job status tracking

docs/subscription-flow.md - Pricing and payment models

docs/api-rest-flow.md - APIKey model usage

docs/training-flow.md - AIModel registry