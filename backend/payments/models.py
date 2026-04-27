# backend/payments/models.py

from django.db import models
from django.conf import settings
import uuid

class SubscriptionPlan(models.Model):
    """Available subscription plans for users"""
    PLAN_TIERS = [
        ('free', 'Free'),
        ('pro', 'Pro'),
        ('business', 'Business'),
    ]
    
    BILLING_PERIODS = [
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
        ('lifetime', 'Lifetime'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50)
    tier = models.CharField(max_length=20, choices=PLAN_TIERS)
    billing_period = models.CharField(max_length=20, choices=BILLING_PERIODS, default='monthly')
    
    # Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default='USD')
    stripe_price_id = models.CharField(max_length=255, null=True, blank=True)
    stripe_product_id = models.CharField(max_length=255, null=True, blank=True)
    
    # Features and limits
    max_minutes_per_month = models.IntegerField(default=60, help_text="Maximum processing minutes per month")
    max_file_size_mb = models.IntegerField(default=100, help_text="Maximum file size in MB")
    max_jobs_per_month = models.IntegerField(default=10)
    concurrent_jobs = models.IntegerField(default=1, help_text="Number of jobs that can run simultaneously")
    
    # Feature flags
    priority_processing = models.BooleanField(default=False)
    subtitle_generation = models.BooleanField(default=False)
    audio_dubbing = models.BooleanField(default=False)
    api_access = models.BooleanField(default=False)
    team_collaboration = models.BooleanField(default=False)
    
    # Features list as JSON (for flexibility)
    features = models.JSONField(default=list, blank=True, help_text="List of features included")
    
    # Availability
    is_active = models.BooleanField(default=True)
    is_public = models.BooleanField(default=True, help_text="Visible on pricing page")
    display_order = models.IntegerField(default=0, help_text="Order on pricing page")
    
    # Metadata
    description = models.TextField(blank=True)
    popular_badge = models.BooleanField(default=False, help_text="Show 'Most Popular' badge")
    savings_percent = models.IntegerField(null=True, blank=True, help_text="Savings percentage for yearly plans")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['display_order', 'price']
    
    def __str__(self):
        return f"{self.name} - {self.billing_period} (${self.price})"


class UserSubscription(models.Model):
    """User's current subscription"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('trialing', 'Trialing'),
        ('past_due', 'Past Due'),
        ('canceled', 'Canceled'),
        ('incomplete', 'Incomplete'),
        ('incomplete_expired', 'Incomplete Expired'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subscription')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True)
    
    # Subscription details
    stripe_subscription_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    stripe_customer_id = models.CharField(max_length=255, null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Dates
    current_period_start = models.DateTimeField()
    current_period_end = models.DateTimeField()
    cancel_at_period_end = models.BooleanField(default=False)
    canceled_at = models.DateTimeField(null=True, blank=True)
    trial_start = models.DateTimeField(null=True, blank=True)
    trial_end = models.DateTimeField(null=True, blank=True)
    
    # Usage
    minutes_used_this_period = models.IntegerField(default=0)
    jobs_used_this_period = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.plan.name if self.plan else 'No Plan'} - {self.status}"
    
    @property
    def is_active(self):
        return self.status in ['active', 'trialing'] and self.current_period_end > timezone.now()
    
    @property
    def remaining_minutes(self):
        if not self.plan:
            return 0
        return max(0, self.plan.max_minutes_per_month - self.minutes_used_this_period)


class PaymentTransaction(models.Model):
    """Track all payment transactions"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('succeeded', 'Succeeded'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
        ('disputed', 'Disputed'),
    ]
    
    PAYMENT_METHODS = [
        ('card', 'Credit Card'),
        ('paypal', 'PayPal'),
        ('mobile_money', 'Mobile Money'),
        ('bank_transfer', 'Bank Transfer'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transactions')
    subscription = models.ForeignKey(UserSubscription, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Payment details
    stripe_payment_intent_id = models.CharField(max_length=255, null=True, blank=True)
    stripe_invoice_id = models.CharField(max_length=255, null=True, blank=True)
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Description
    description = models.CharField(max_length=255, blank=True)
    invoice_url = models.URLField(null=True, blank=True)
    receipt_url = models.URLField(null=True, blank=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    
    # Timestamps
    paid_at = models.DateTimeField(null=True, blank=True)
    refunded_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - ${self.amount} - {self.status}"


class Invoice(models.Model):
    """Invoice records for billing"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('paid', 'Paid'),
        ('uncollectible', 'Uncollectible'),
        ('void', 'Void'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='invoices')
    subscription = models.ForeignKey(UserSubscription, on_delete=models.SET_NULL, null=True)
    transaction = models.OneToOneField(PaymentTransaction, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Invoice details
    invoice_number = models.CharField(max_length=100, unique=True)
    stripe_invoice_id = models.CharField(max_length=255, null=True, blank=True)
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Period
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    
    # URLs
    pdf_url = models.URLField(null=True, blank=True)
    hosted_invoice_url = models.URLField(null=True, blank=True)
    
    # Dates
    due_date = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.user.email} - ${self.total}"


class PromoCode(models.Model):
    """Promotional codes and discounts"""
    DISCOUNT_TYPES = [
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, help_text="Percentage or fixed amount")
    
    # Applicable plans (empty means all plans)
    applicable_plans = models.ManyToManyField(SubscriptionPlan, blank=True)
    
    # Usage limits
    max_uses = models.IntegerField(null=True, blank=True)
    used_count = models.IntegerField(default=0)
    max_uses_per_user = models.IntegerField(default=1)
    
    # Validity
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    
    # Metadata
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_codes')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.code} - {self.discount_value}{'%' if self.discount_type == 'percentage' else '$'}"
    
    @property
    def is_valid(self):
        now = timezone.now()
        return (self.is_active and 
                self.valid_from <= now <= self.valid_to and
                (self.max_uses is None or self.used_count < self.max_uses))


class PaymentMethod(models.Model):
    """Saved payment methods for users"""
    TYPE_CHOICES = [
        ('card', 'Card'),
        ('paypal', 'PayPal'),
        ('mobile_money', 'Mobile Money'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payment_methods')
    
    # Payment method details
    stripe_payment_method_id = models.CharField(max_length=255, unique=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    is_default = models.BooleanField(default=False)
    
    # Card details (masked)
    card_last4 = models.CharField(max_length=4, null=True, blank=True)
    card_brand = models.CharField(max_length=50, null=True, blank=True)
    card_exp_month = models.IntegerField(null=True, blank=True)
    card_exp_year = models.IntegerField(null=True, blank=True)
    
    # Billing details
    billing_email = models.EmailField(null=True, blank=True)
    billing_name = models.CharField(max_length=255, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_default', '-created_at']
    
    def __str__(self):
        if self.type == 'card':
            return f"{self.user.email} - {self.card_brand} ending in {self.card_last4}"
        return f"{self.user.email} - {self.type}"


class UsageRecord(models.Model):
    """Track detailed usage for billing"""
    USAGE_TYPES = [
        ('processing_minutes', 'Processing Minutes'),
        ('file_upload', 'File Upload'),
        ('api_call', 'API Call'),
        ('subtitle_generation', 'Subtitle Generation'),
        ('audio_dubbing', 'Audio Dubbing'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='usage_records')
    subscription = models.ForeignKey(UserSubscription, on_delete=models.CASCADE, related_name='usage_records')
    job = models.ForeignKey('jobs.Job', on_delete=models.SET_NULL, null=True, blank=True)
    
    usage_type = models.CharField(max_length=50, choices=USAGE_TYPES)
    quantity = models.FloatField(help_text="Amount used (minutes, count, etc.)")
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['subscription', 'usage_type']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.usage_type}: {self.quantity}"
