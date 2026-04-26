# backend/pricing/stripe_utils.py

import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY


def create_stripe_product(plan):
    """Create or update a Stripe product for a plan"""
    if plan.stripe_price_id:
        return plan.stripe_price_id

    try:
        product = stripe.Product.create(
            name=f"{plan.name} - {plan.get_billing_period_display()}",
            description=f"{plan.get_tier_display()} plan",
            metadata={'plan_id': str(plan.id)},
        )

        price = stripe.Price.create(
            product=product.id,
            unit_amount=int(plan.price * 100),  # Convert to cents
            currency='usd',
            recurring={'interval': 'month' if plan.billing_period == 'monthly' else 'year'},
        )

        plan.stripe_price_id = price.id
        plan.save(update_fields=['stripe_price_id'])
        return price.id
    except stripe.error.StripeError as e:
        return None


def update_stripe_product(plan):
    """Sync plan changes to Stripe"""
    if not plan.stripe_price_id:
        return create_stripe_product(plan)
    return plan.stripe_price_id
