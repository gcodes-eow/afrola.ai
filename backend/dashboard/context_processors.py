# backend/dashboard/context_processors.py

from django.conf import settings


def user_subscription_info(request):
    """Add user subscription info to all template contexts"""
    context = {
        'SITE_NAME': settings.SITE_NAME,
        'SITE_DESCRIPTION': settings.SITE_DESCRIPTION,
    }

    if request.user.is_authenticated:
        subscription = getattr(request.user, 'subscription', None)
        context.update({
            'user_subscription': subscription,
            'subscription_tier': request.user.subscription_tier,
            'is_free_tier': request.user.subscription_tier == 'free',
            'is_pro_tier': request.user.subscription_tier == 'pro',
            'is_enterprise_tier': request.user.subscription_tier == 'enterprise',
        })

        if subscription:
            context.update({
                'minutes_used': subscription.minutes_used_this_period,
                'minutes_limit': subscription.plan.max_minutes_per_month if subscription.plan else 0,
                'jobs_used': subscription.jobs_used_this_period,
                'jobs_limit': subscription.plan.max_jobs_per_month if subscription.plan else 0,
            })

    return context