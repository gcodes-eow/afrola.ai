# backend/payments/urls.py

from django.urls import path
from . import views
from . import webhooks

app_name = 'payments'

urlpatterns = [
    path('checkout/<uuid:plan_id>/', views.create_checkout_session_view, name='checkout'),
    path('billing/', views.billing_view, name='billing'),
    path('cancel/', views.cancel_subscription_view, name='cancel_subscription'),
    path('history/', views.payment_history_view, name='payment_history'),
    path('webhook/', webhooks.stripe_webhook, name='stripe_webhook'),
]
