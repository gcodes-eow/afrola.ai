# backend/payments/views.py

import stripe
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from pricing.models import PricingPlan
from payments.models import UserSubscription, PaymentTransaction
from payments.stripe_utils import create_checkout_session

stripe.api_key = settings.STRIPE_SECRET_KEY


@login_required
def create_checkout_session_view(request, plan_id):
    """Create Stripe Checkout session for subscription"""
    plan = get_object_or_404(PricingPlan, id=plan_id, is_active=True)

    if plan.price == 0:
        # Free plan — activate immediately
        subscription, _ = UserSubscription.objects.update_or_create(
            user=request.user,
            defaults={
                'plan': plan,
                'status': 'active',
                'current_period_start': timezone.now(),
                'current_period_end': timezone.now() + timezone.timedelta(days=36500),
            }
        )
        request.user.subscription_tier = plan.tier
        request.user.save()
        messages.success(request, f'You are now on the {plan.name} plan!')
        return redirect('dashboard:index')

    try:
        # Create Stripe Checkout session
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': plan.stripe_price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=request.build_absolute_uri('/dashboard/billing/?success=true'),
            cancel_url=request.build_absolute_uri('/pricing/'),
            customer_email=request.user.email,
            metadata={
                'user_id': str(request.user.id),
                'plan_id': str(plan.id),
            },
        )
        return redirect(session.url)
    except stripe.error.StripeError as e:
        messages.error(request, f'Payment error: {str(e)}')
        return redirect('pricing:index')


@login_required
def billing_view(request):
    """Show billing and subscription management"""
    subscription = getattr(request.user, 'subscription', None)
    transactions = PaymentTransaction.objects.filter(user=request.user).order_by('-created_at')[:10]
    plans = PricingPlan.objects.filter(is_active=True).order_by('tier')

    context = {
        'subscription': subscription,
        'transactions': transactions,
        'plans': plans,
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
    }
    return render(request, 'dashboard/billing.html', context)


@login_required
def cancel_subscription_view(request):
    """Cancel user's subscription"""
    subscription = getattr(request.user, 'subscription', None)
    if subscription and subscription.status == 'active':
        subscription.cancel_at_period_end = True
        subscription.save()

        # Cancel in Stripe if it exists
        if subscription.stripe_subscription_id:
            try:
                stripe.Subscription.modify(
                    subscription.stripe_subscription_id,
                    cancel_at_period_end=True
                )
            except stripe.error.StripeError:
                pass

        messages.success(request, 'Your subscription has been canceled and will end at the current billing period.')
    else:
        messages.error(request, 'No active subscription to cancel.')

    return redirect('dashboard:billing_view')


@login_required
def payment_history_view(request):
    """Show payment transaction history"""
    transactions = PaymentTransaction.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'dashboard/billing.html', {'transactions': transactions})
