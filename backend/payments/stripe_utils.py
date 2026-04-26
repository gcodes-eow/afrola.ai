# backend/payments/stripe_utils.py

import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY


def create_checkout_session(plan, user, success_url, cancel_url):
    """Create a Stripe Checkout session for a subscription plan"""
    if not plan.stripe_price_id:
        raise ValueError(f"Plan {plan.name} has no Stripe price ID")

    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price': plan.stripe_price_id,
            'quantity': 1,
        }],
        mode='subscription',
        success_url=success_url,
        cancel_url=cancel_url,
        customer_email=user.email,
        metadata={
            'user_id': str(user.id),
            'plan_id': str(plan.id),
        },
    )
    return session


def get_customer_subscription(stripe_customer_id):
    """Get active stripe subscription for a customer"""
    try:
        subscriptions = stripe.Subscription.list(
            customer=stripe_customer_id,
            status='active',
            limit=1,
        )
        return subscriptions.data[0] if subscriptions.data else None
    except stripe.error.StripeError:
        return None


def cancel_subscription(stripe_subscription_id):
    """Cancel a Stripe subscription"""
    try:
        stripe.Subscription.modify(
            stripe_subscription_id,
            cancel_at_period_end=True,
        )
        return True
    except stripe.error.StripeError as e:
        return False
