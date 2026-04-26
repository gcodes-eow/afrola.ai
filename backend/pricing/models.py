# backend/pricing/models.py
from django.db import models
import uuid


class PricingPlan(models.Model):
    """Available subscription plans"""

    TIER_CHOICES = [
        ('free', 'Free'),
        ('pro', 'Pro'),
        ('enterprise', 'Enterprise'),
    ]

    BILLING_PERIODS = [
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50)
    tier = models.CharField(max_length=20, choices=TIER_CHOICES)
    billing_period = models.CharField(max_length=20, choices=BILLING_PERIODS, default='monthly')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Limits
    max_minutes_per_month = models.IntegerField(default=60)
    max_file_size_mb = models.IntegerField(default=100)
    max_jobs_per_month = models.IntegerField(default=10)
    concurrent_jobs = models.IntegerField(default=1)

    # Features list as JSON for flexibility
    features = models.JSONField(default=list)

    # Availability
    is_active = models.BooleanField(default=True)

    # Stripe integration
    stripe_price_id = models.CharField(max_length=255, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['price', 'billing_period']

    def __str__(self):
        return f"{self.name} ({self.get_tier_display()}) - ${self.price}/{self.billing_period}"