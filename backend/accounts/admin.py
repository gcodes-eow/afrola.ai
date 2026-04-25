from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'full_name', 'subscription_tier', 'created_at')
    list_filter = ('subscription_tier', 'is_staff')
    search_fields = ('email', 'full_name')
    
    fieldsets = UserAdmin.fieldsets + (
        ('Subscription Info', {
            'fields': ('subscription_tier', 'monthly_processing_seconds', 'monthly_jobs_count')
        }),
    )
