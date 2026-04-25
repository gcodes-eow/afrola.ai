from django.contrib import admin
from .models import PricingPlan

@admin.register(PricingPlan)
class PricingPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'price_monthly', 'max_minutes_per_month', 'is_active')
    list_filter = ('is_active',)
