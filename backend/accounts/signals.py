# backend/accounts/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import User


@receiver(post_save, sender=User)
def create_dashboard_on_user_creation(sender, instance, created, **kwargs):
    """Create dashboard and assign free subscription when user is created"""
    if created:
        # Create dashboard
        from dashboard.models import UserDashboard, UserAnalytics
        UserDashboard.objects.get_or_create(user=instance)
        UserAnalytics.objects.get_or_create(user=instance)

        # Assign free plan
        from payments.models import SubscriptionPlan, UserSubscription
        from django.utils import timezone

        free_plan = SubscriptionPlan.objects.filter(tier='free', is_active=True).first()
        if free_plan:
            UserSubscription.objects.create(
                user=instance,
                plan=free_plan,
                status='active',
                current_period_start=timezone.now(),
                current_period_end=timezone.now() + timezone.timedelta(days=36500),  # ~100 years
            )