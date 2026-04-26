# backend/payments/webhooks.py

import stripe
import json
import logging
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from pricing.models import PricingPlan
from payments.models import UserSubscription, PaymentTransaction

logger = logging.getLogger(__name__)
stripe.api_key = settings.STRIPE_SECRET_KEY


@csrf_exempt
def stripe_webhook(request):
    """Handle Stripe webhook events"""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)

    # Handle events
    event_handlers = {
        'checkout.session.completed': _handle_checkout_completed,
        'customer.subscription.updated': _handle_subscription_updated,
        'customer.subscription.deleted': _handle_subscription_deleted,
        'invoice.payment_succeeded': _handle_payment_succeeded,
        'invoice.payment_failed': _handle_payment_failed,
    }

    handler = event_handlers.get(event['type'])
    if handler:
        handler(event['data']['object'])
    else:
        logger.info(f"Unhandled webhook event: {event['type']}")

    return HttpResponse(status=200)


def _handle_checkout_completed(session):
    """Handle successful checkout — create subscription"""
    metadata = session.get('metadata', {})
    user_id = metadata.get('user_id')
    plan_id = metadata.get('plan_id')

    if not user_id or not plan_id:
        logger.error("Missing user_id or plan_id in checkout metadata")
        return

    from accounts.models import User
    try:
        user = User.objects.get(id=user_id)
        plan = PricingPlan.objects.get(id=plan_id)

        # Create or update subscription
        subscription, _ = UserSubscription.objects.update_or_create(
            user=user,
            defaults={
                'plan': plan,
                'stripe_subscription_id': session.get('subscription'),
                'stripe_customer_id': session.get('customer'),
                'status': 'active',
                'current_period_start': timezone.now(),
                'current_period_end': timezone.now() + timezone.timedelta(days=30),
            }
        )

        # Update user tier
        user.subscription_tier = plan.tier
        user.stripe_customer_id = session.get('customer')
        user.save()

        logger.info(f"Subscription created for {user.email} on {plan.name} plan")
    except (User.DoesNotExist, PricingPlan.DoesNotExist) as e:
        logger.error(f"Error creating subscription: {e}")


def _handle_subscription_updated(subscription_data):
    """Handle subscription updates from Stripe"""
    try:
        subscription = UserSubscription.objects.get(
            stripe_subscription_id=subscription_data['id']
        )
        subscription.status = subscription_data.get('status', subscription.status)
        subscription.cancel_at_period_end = subscription_data.get('cancel_at_period_end', False)
        if subscription_data.get('canceled_at'):
            subscription.canceled_at = timezone.datetime.fromtimestamp(
                subscription_data['canceled_at'], tz=timezone.utc
            )

        # Update period dates
        if subscription_data.get('current_period_start'):
            subscription.current_period_start = timezone.datetime.fromtimestamp(
                subscription_data['current_period_start'], tz=timezone.utc
            )
        if subscription_data.get('current_period_end'):
            subscription.current_period_end = timezone.datetime.fromtimestamp(
                subscription_data['current_period_end'], tz=timezone.utc
            )

        subscription.save()
        logger.info(f"Subscription updated for {subscription.user.email}")
    except UserSubscription.DoesNotExist:
        logger.warning(f"Subscription not found: {subscription_data['id']}")


def _handle_subscription_deleted(subscription_data):
    """Handle subscription cancellation — downgrade to free"""
    try:
        subscription = UserSubscription.objects.get(
            stripe_subscription_id=subscription_data['id']
        )
        subscription.status = 'canceled'
        subscription.canceled_at = timezone.now()
        subscription.save()

        # Downgrade user to free
        free_plan = PricingPlan.objects.filter(tier='free', is_active=True).first()
        user = subscription.user
        user.subscription_tier = 'free'
        user.save()

        if free_plan:
            # Create new free subscription
            UserSubscription.objects.create(
                user=user,
                plan=free_plan,
                status='active',
                current_period_start=timezone.now(),
                current_period_end=timezone.now() + timezone.timedelta(days=36500),
            )

        logger.info(f"Subscription deleted for {user.email}, downgraded to free")
    except UserSubscription.DoesNotExist:
        logger.warning(f"Subscription not found for deletion: {subscription_data['id']}")


def _handle_payment_succeeded(invoice):
    """Record successful payment"""
    _record_payment(invoice, 'succeeded')


def _handle_payment_failed(invoice):
    """Record failed payment"""
    _record_payment(invoice, 'failed')


def _record_payment(invoice, status):
    """Create payment transaction record"""
    from accounts.models import User

    customer_id = invoice.get('customer')
    if not customer_id:
        return

    try:
        user = User.objects.get(stripe_customer_id=customer_id)

        PaymentTransaction.objects.create(
            user=user,
            amount=invoice.get('amount_paid', 0) / 100,
            currency=invoice.get('currency', 'usd').upper(),
            payment_method='card',
            status=status,
            stripe_payment_intent_id=invoice.get('payment_intent'),
            stripe_invoice_id=invoice.get('id'),
            description=f"Invoice {invoice.get('number', '')}",
            invoice_url=invoice.get('hosted_invoice_url', ''),
            paid_at=timezone.now() if status == 'succeeded' else None,
        )

        logger.info(f"Payment recorded for {user.email}: {status}")
    except User.DoesNotExist:
        logger.warning(f"User not found for stripe customer: {customer_id}")
