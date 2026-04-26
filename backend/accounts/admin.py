# backend/accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'full_name', 'subscription_tier', 'is_active', 'created_at')
    list_filter = ('subscription_tier', 'is_staff', 'is_active')
    search_fields = ('email', 'full_name')
    
    fieldsets = UserAdmin.fieldsets + (
        ('Subscription Info', {
            'fields': (
                'subscription_tier',
                'subscription_end_date',
                'stripe_customer_id',
                'monthly_processing_seconds',
                'monthly_jobs_count',
            )
        }),
        ('Verification', {
            'fields': (
                'email_verified',
                'email_verification_token',
            )
        }),
        ('Profile', {
            'fields': ('avatar',)
        }),
    )