# backend/accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid


class User(AbstractUser):
    """Extended user model with subscription and usage tracking"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)

    # NEW: Avatar
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)

    # Subscription
    subscription_tier = models.CharField(
        max_length=20,
        choices=[
            ('free', 'Free'),
            ('pro', 'Pro'),
            ('enterprise', 'Enterprise')
        ],
        default='free'
    )
    # NEW: Subscription end date
    subscription_end_date = models.DateTimeField(null=True, blank=True)
    # NEW: Stripe customer ID for payment integration
    stripe_customer_id = models.CharField(max_length=255, null=True, blank=True)

    # Usage tracking
    monthly_processing_seconds = models.BigIntegerField(default=0)
    monthly_jobs_count = models.IntegerField(default=0)
    # NEW: Track when usage counters were last reset
    last_reset_date = models.DateField(auto_now_add=True)

    # NEW: Email verification
    email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=255, null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'full_name']

    class Meta:
        # NEW: Indexes for query performance
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['subscription_tier']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return self.email