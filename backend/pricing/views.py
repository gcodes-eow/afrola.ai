# backend/pricing/views.py

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import PricingPlan


def pricing_index(request):
    """Display all available pricing plans"""
    plans = PricingPlan.objects.filter(is_active=True)

    # Group by tier - keep model's default ordering (by price)
    monthly_plans = plans.filter(billing_period='monthly')
    yearly_plans = plans.filter(billing_period='yearly')

    context = {
        'monthly_plans': monthly_plans,
        'yearly_plans': yearly_plans,
    }
    return render(request, 'pricing/index.html', context)
