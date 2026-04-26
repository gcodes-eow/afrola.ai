# backend/accounts/decorators.py

from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import user_passes_test
from functools import wraps


def subscription_required(tier):
    """Require minimum subscription tier to access view"""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                raise PermissionDenied

            tier_hierarchy = {'free': 0, 'pro': 1, 'enterprise': 2}
            user_tier = request.user.subscription_tier

            if tier_hierarchy.get(user_tier, 0) < tier_hierarchy.get(tier, 0):
                raise PermissionDenied("You need a higher subscription tier to access this feature.")

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def email_verified_required(view_func):
    """Require verified email to access view"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise PermissionDenied
        if not request.user.email_verified:
            raise PermissionDenied("Please verify your email address first.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view