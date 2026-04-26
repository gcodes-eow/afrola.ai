# backend/accounts/tasks.py
"""Periodic tasks related to user accounts and usage."""
from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from accounts.models import User
import logging

logger = logging.getLogger(__name__)


@shared_task
def reset_monthly_usage_task():
    """
    Reset monthly usage counters for all users.
    Runs on the 1st of every month via Celery Beat.
    """
    first_of_month = timezone.now().replace(day=1)
    users_updated = User.objects.update(
        monthly_processing_seconds=0,
        monthly_jobs_count=0,
        last_reset_date=first_of_month.date()
    )
    logger.info(f"Monthly usage reset for {users_updated} users")
    return {'users_updated': users_updated}


@shared_task
def send_usage_warnings():
    """
    Warn users approaching their monthly limits.
    Runs daily at noon via Celery Beat.
    """
    from payments.models import UserSubscription

    subscriptions = UserSubscription.objects.filter(
        status='active'
    ).select_related('user', 'plan')

    warnings_sent = 0
    for sub in subscriptions:
        if not sub.plan:
            continue

        # Check if user is at 80%+ of their limit
        minutes_limit = sub.plan.max_minutes_per_month
        jobs_limit = sub.plan.max_jobs_per_month

        minutes_pct = (sub.minutes_used_this_period / minutes_limit * 100) if minutes_limit else 0
        jobs_pct = (sub.jobs_used_this_period / jobs_limit * 100) if jobs_limit else 0

        if minutes_pct >= 80 or jobs_pct >= 80:
            _send_limit_warning_email(sub.user, minutes_pct, jobs_pct)
            warnings_sent += 1

    logger.info(f"Usage warnings sent to {warnings_sent} users")
    return {'warnings_sent': warnings_sent}


@shared_task
def send_notification_task(user_id, message):
    """Send email notification to a user"""
    try:
        user = User.objects.get(id=user_id)
        send_mail(
            subject=f'Notification from {settings.SITE_NAME}',
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
        )
        logger.info(f"Notification sent to {user.email}")
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found for notification")


def _send_limit_warning_email(user, minutes_pct, jobs_pct):
    """Send email warning about approaching limits"""
    subject = f'You are approaching your limit on {settings.SITE_NAME}'
    message = (
        f"Hi {user.full_name},\n\n"
        f"You're approaching your monthly limits:\n"
        f"- Processing minutes: {minutes_pct:.0f}% used\n"
        f"- Jobs: {jobs_pct:.0f}% used\n\n"
        f"Consider upgrading your plan for more capacity.\n"
        f"View plans: {settings.FRONTEND_URL}/pricing/\n\n"
        f"Thanks,\n{settings.SITE_NAME} Team"
    )
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )