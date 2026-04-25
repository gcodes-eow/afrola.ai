docs/subscription-flow.md

# Subscription & Payment Flow — Afrola.ai (Django + Stripe + Mobile Money)

## Purpose
Define how users subscribe to plans, make payments using Stripe and mobile money (Airtel/MTN), and track usage for enforcement.

## Flow Overview
Select Plan → Payment → Webhook → Subscription → Usage → Limits
↓ ↓ ↓ ↓ ↓ ↓
Pricing Stripe/ Callback DB Update Track Enforce
Mobile
Money

text

## Architecture Components

| Component | Location | Purpose |
|-----------|----------|---------|
| Plan Model | `pricing/models.py` | Subscription tiers definition |
| Subscription Model | `payments/models.py` | User subscription records |
| Transaction Model | `payments/models.py` | Payment transaction logs |
| Usage Model | `jobs/models.py` | Monthly usage tracking |
| Stripe Views | `payments/views.py` | Checkout session creation |
| Webhook Handler | `payments/webhooks.py` | Stripe payment callbacks |
| Mobile Money | `utils/mobile_money.py` | Airtel/MTN API integration |
| Limits Enforcement | `jobs/forms.py` | Job creation validation |
| Templates | `templates/pricing/` | Pricing page, checkout |

## Required Files

### Pricing App
backend/pricing/
├── init.py # ✅
├── admin.py # ⏳ Plan admin interface
├── apps.py # ✅ App config
├── models.py # ⏳ PricingPlan model
├── urls.py # ⏳ /pricing/ routes
├── views.py # ⏳ Plan listing view
├── utils.py # ⏳ Plan helpers (features list)
├── tests.py # ⏳ Pricing tests
├── stripe_utils.py # ⏳ Stripe product sync
└── webhooks.py # ⏳ Webhook handlers

text

### Payments App
backend/payments/
├── init.py # ✅
├── admin.py # ⏳ Payment admin
├── apps.py # ✅ App config
├── models.py # ⏳ UserSubscription, Transaction
├── urls.py # ⏳ Checkout, webhook routes
├── views.py # ⏳ CreateCheckoutSession
├── tests.py # ⏳ Payment tests
├── webhooks.py # ⏳ Stripe webhook handler
└── stripe_utils.py # ⏳ Stripe API helpers

text

### Jobs App (Usage Tracking)
backend/jobs/
├── models.py # ✅ Job model with duration tracking
├── forms.py # ⏳ Job creation with quota check
├── utils.py # ⏳ Usage calculation helpers
└── admin.py # ✅ Usage stats in admin

text

### Dashboard App (User-facing)
backend/dashboard/
├── views.py # ⏳ Billing management view
├── context_processors.py # ⏳ Subscription info for templates
└── urls.py # ⏳ /billing/ route

text

### Utilities
backend/utils/
├── mobile_money.py # ⏳ Airtel/MTN API integration
├── validators.py # ⏳ Phone number validation
└── init.py # ✅

text

### Templates
backend/templates/pricing/
├── index.html # ⏳ Pricing page with plan cards
└── checkout.html # ⏳ Checkout form

backend/templates/dashboard/
├── billing.html # ⏳ Subscription management
├── usage_stats.html # ⏳ Usage statistics widget
└── index.html # ⏳ Dashboard with usage widget

backend/templates/includes/
└── subscription_banner.html # ⏳ Upgrade banner for free users

text

## Implementation Plan

### Batch 1: Pricing Plans Foundation
**Files to create:**
- `pricing/models.py` - PricingPlan model
- `pricing/admin.py` - Plan management
- `pricing/utils.py` - Feature list helpers
- `fixtures/initial_plans.json` - Seed data

**Plan Structure:**
```python
class PricingPlan(models.Model):
    name = models.CharField(max_length=50)  # Free, Pro, Enterprise
    tier = models.CharField(choices=TIER_CHOICES)
    price_monthly = models.DecimalField()
    price_yearly = models.DecimalField(null=True)
    max_minutes_per_month = models.IntegerField()
    max_file_size_mb = models.IntegerField()
    max_jobs_per_month = models.IntegerField()
    concurrent_jobs = models.IntegerField(default=1)
    features = models.JSONField(default=list)
    stripe_price_id = models.CharField(max_length=255, null=True)
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)
Seed Data:

json
[
  {"name": "Free", "tier": "free", "price_monthly": 0, "max_minutes_per_month": 60},
  {"name": "Pro", "tier": "pro", "price_monthly": 29.99, "max_minutes_per_month": 600},
  {"name": "Enterprise", "tier": "enterprise", "price_monthly": 99.99, "max_minutes_per_month": 3000}
]
Batch 2: Stripe Integration
Files to create:

payments/stripe_utils.py - Stripe API helpers

payments/views.py - CreateCheckoutSession view

payments/urls.py - Checkout routes

templates/pricing/checkout.html

Environment Variables:

bash
STRIPE_PUBLIC_KEY=pk_test_xxx
STRIPE_SECRET_KEY=sk_test_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
Checkout Flow:

User selects plan

POST to /payments/create-checkout-session/

Stripe session created

Redirect to Stripe checkout

User completes payment

Redirect to success/cancel URL

Batch 3: Webhook Handling
Files to create:

payments/webhooks.py - Webhook endpoint

pricing/webhooks.py - Plan sync webhooks

payments/urls.py - /payments/webhook/ route

Webhook Events to Handle:

Event	Action
checkout.session.completed	Create/activate subscription
customer.subscription.updated	Update plan, dates
customer.subscription.deleted	Downgrade to free
invoice.payment_succeeded	Record payment transaction
invoice.payment_failed	Notify user, mark past_due
customer.subscription.trial_will_end	Send reminder email
Batch 4: User Subscription Model
Files to create:

payments/models.py - UserSubscription model

payments/models.py - PaymentTransaction model

payments/admin.py - Subscription admin

UserSubscription Fields:

python
class UserSubscription(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    plan = models.ForeignKey(PricingPlan, on_delete=models.PROTECT)
    stripe_subscription_id = models.CharField(unique=True)
    status = models.CharField(max_length=20)  # active, past_due, canceled, trialing
    current_period_start = models.DateTimeField()
    current_period_end = models.DateTimeField()
    cancel_at_period_end = models.BooleanField(default=False)
    trial_start = models.DateTimeField(null=True)
    trial_end = models.DateTimeField(null=True)
Batch 5: Usage Tracking & Enforcement
Files to create/update:

jobs/utils.py - Usage calculation

jobs/forms.py - Job creation with quota check

accounts/signals.py - Reset monthly usage

dashboard/context_processors.py - Usage stats for templates

Usage Tracking Logic:

python
# In Job creation
def check_quota(user, duration_seconds):
    subscription = user.subscription
    current_usage = user.monthly_processing_seconds
    limit = subscription.plan.max_minutes_per_month * 60
    return (current_usage + duration_seconds) <= limit
Reset Job (Celery Beat):

python
@shared_task
def reset_monthly_usage():
    User.objects.update(
        monthly_processing_seconds=0,
        monthly_jobs_count=0,
        last_reset_date=timezone.now().replace(day=1)
    )
Batch 6: Mobile Money Integration (Airtel/MTN)
Files to create:

utils/mobile_money.py - AirtelMoney, MTNMoney classes

payments/views.py - initiate_mobile_payment view

payments/webhooks.py - mobile_money_callback handler

templates/payment/mobile_checkout.html

Supported Providers:

Provider	Countries	API Type
Airtel Money	UG, KE, TZ, RW, MW, ZM, ZW	REST API
MTN Money	UG, CM, CI, ZM, RW, BF, BJ, GA, GH, GW, ML, NE, CG, CD	REST API
Mobile Money Flow:

User enters phone number

System detects provider (Airtel/MTN)

Initiates payment request

User approves on phone

Webhook receives confirmation

Subscription activated

Batch 7: Subscription Management UI
Files to create:

dashboard/views.py - billing_view, cancel_subscription

dashboard/urls.py - /billing/ routes

templates/dashboard/billing.html

templates/dashboard/usage_stats.html

Features:

View current plan and usage

Upgrade/downgrade plans

Cancel subscription

View payment history

Download invoices

Update payment method

Batch 8: Admin Dashboard
Files to create:

pricing/admin.py - Plan management

payments/admin.py - Subscription overview

accounts/admin.py - User subscription inline

Admin Views:

MRR (Monthly Recurring Revenue) chart

Subscription counts by plan

Failed payments list

Usage outliers

Trial expiring soon

Dependencies
txt
# requirements.txt additions
stripe==7.4.0
requests==2.31.0
django-celery-beat==2.5.0
Environment Variables
bash
# Stripe
STRIPE_PUBLIC_KEY=pk_test_xxx
STRIPE_SECRET_KEY=sk_test_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx

# Airtel Mobile Money
AIRTEL_MONEY_ENABLED=True
AIRTEL_MONEY_API_URL=https://openapi.airtel.africa
AIRTEL_MONEY_CLIENT_ID=xxx
AIRTEL_MONEY_CLIENT_SECRET=xxx
AIRTEL_MONEY_API_KEY=xxx
AIRTEL_MONEY_PIN=xxx
AIRTEL_MONEY_COUNTRY=UG
AIRTEL_MONEY_CURRENCY=UGX

# MTN Mobile Money
MTN_MONEY_ENABLED=True
MTN_MONEY_API_URL=https://sandbox.mtn.com/collection/v1_0
MTN_MONEY_SUBSCRIPTION_KEY=xxx
MTN_MONEY_API_USER=xxx
MTN_MONEY_API_KEY=xxx
MTN_MONEY_PIN=xxx
MTN_MONEY_COUNTRY=UG
MTN_MONEY_CURRENCY=UGX
MTN_MONEY_CALLBACK_URL=https://api.afrola.ai/payments/mtn-webhook/

# Payment Settings
PAYMENT_PROVIDERS=stripe,airtel_money,mtn_money
PAYMENT_EXPIRY_TIME=300
PAYMENT_CONFIRMATION_TIMEOUT=60
Verification Checklist
Pricing plans visible in Django admin

Pricing page shows all active plans

Checkout session creates Stripe payment link

Webhook creates subscription after payment

User has subscription record in DB

Usage limits enforced on job creation

Dashboard shows usage stats

Upgrade/downgrade workflow works

Cancel subscription works

Mobile money integration (if enabled)

Monthly usage reset works (Celery Beat)

Admin can view subscription analytics

API Endpoints (for frontend)
Method	Endpoint	Description
GET	/api/plans/	List subscription plans
GET	/api/subscription/	Get current user subscription
POST	/api/subscription/	Create/update subscription
DELETE	/api/subscription/	Cancel subscription
POST	/api/subscription/webhook/	Stripe webhook receiver
POST	/api/payments/mobile/	Initiate mobile money payment
GET	/api/usage/	Get current usage stats
Related Documentation
docs/user-auth-flow.md - User registration (auto-assigns free plan)

docs/celery-queue-flow.md - Monthly usage reset task

docs/database-schema.md - Subscription models

docs/api-rest-flow.md - Subscription API endpoints