# backend/pricing/admin.py
from django.contrib import admin
from .models import PricingPlan

@admin.register(PricingPlan)
class PricingPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'tier', 'billing_period', 'price', 'max_minutes_per_month', 'is_active')
    list_filter = ('is_active', 'tier', 'billing_period')
    search_fields = ('name',)