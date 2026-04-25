# backend/payments/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import (
    SubscriptionPlan, UserSubscription, PaymentTransaction, 
    Invoice, PromoCode, PaymentMethod, UsageRecord
)

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'tier', 'billing_period', 'price', 'max_minutes_per_month', 'is_active', 'popular_badge')
    list_filter = ('tier', 'billing_period', 'is_active', 'is_public')
    search_fields = ('name', 'description')
    list_editable = ('is_active', 'price')
    ordering = ('display_order', 'price')
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'tier', 'billing_period', 'description', 'display_order')
        }),
        ('Pricing', {
            'fields': ('price', 'currency', 'stripe_price_id', 'stripe_product_id')
        }),
        ('Limits', {
            'fields': ('max_minutes_per_month', 'max_file_size_mb', 'max_jobs_per_month', 'concurrent_jobs')
        }),
        ('Features', {
            'fields': ('priority_processing', 'subtitle_generation', 'audio_dubbing', 
                      'api_access', 'team_collaboration', 'features')
        }),
        ('Display', {
            'fields': ('is_active', 'is_public', 'popular_badge', 'savings_percent')
        }),
    )

@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'status', 'current_period_end', 'minutes_used_this_period', 'is_active')
    list_filter = ('status', 'plan__tier', 'cancel_at_period_end')
    search_fields = ('user__email', 'stripe_subscription_id')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('User & Plan', {
            'fields': ('user', 'plan', 'status')
        }),
        ('Stripe Details', {
            'fields': ('stripe_subscription_id', 'stripe_customer_id')
        }),
        ('Period', {
            'fields': ('current_period_start', 'current_period_end', 'trial_start', 'trial_end')
        }),
        ('Cancellation', {
            'fields': ('cancel_at_period_end', 'canceled_at')
        }),
        ('Usage', {
            'fields': ('minutes_used_this_period', 'jobs_used_this_period')
        }),
    )

@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'amount', 'currency', 'status', 'payment_method', 'created_at')
    list_filter = ('status', 'payment_method', 'currency')
    search_fields = ('user__email', 'stripe_payment_intent_id')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Transaction Info', {
            'fields': ('user', 'subscription', 'amount', 'currency', 'payment_method', 'status')
        }),
        ('Stripe Details', {
            'fields': ('stripe_payment_intent_id', 'stripe_invoice_id')
        }),
        ('Additional Info', {
            'fields': ('description', 'invoice_url', 'receipt_url', 'metadata', 'error_message')
        }),
        ('Timestamps', {
            'fields': ('paid_at', 'refunded_at')
        }),
    )

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'user', 'amount', 'total', 'status', 'period_start', 'period_end')
    list_filter = ('status',)
    search_fields = ('invoice_number', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Invoice Info', {
            'fields': ('invoice_number', 'user', 'subscription', 'transaction', 'status')
        }),
        ('Amounts', {
            'fields': ('amount', 'tax', 'total')
        }),
        ('Period', {
            'fields': ('period_start', 'period_end', 'due_date')
        }),
        ('Links', {
            'fields': ('pdf_url', 'hosted_invoice_url')
        }),
        ('Timestamps', {
            'fields': ('paid_at',)
        }),
    )

@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_type', 'discount_value', 'valid_from', 'valid_to', 'used_count', 'is_active')
    list_filter = ('discount_type', 'is_active')
    search_fields = ('code', 'description')
    filter_horizontal = ('applicable_plans',)
    
    fieldsets = (
        ('Code Info', {
            'fields': ('code', 'description', 'discount_type', 'discount_value')
        }),
        ('Applicability', {
            'fields': ('applicable_plans',)
        }),
        ('Usage Limits', {
            'fields': ('max_uses', 'used_count', 'max_uses_per_user')
        }),
        ('Validity', {
            'fields': ('valid_from', 'valid_to', 'is_active')
        }),
        ('Metadata', {
            'fields': ('created_by',)
        }),
    )

@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('user', 'type', 'card_brand', 'card_last4', 'is_default', 'created_at')
    list_filter = ('type', 'card_brand', 'is_default')
    search_fields = ('user__email', 'card_last4')
    
    fieldsets = (
        ('User Info', {
            'fields': ('user', 'type', 'is_default')
        }),
        ('Card Details', {
            'fields': ('card_last4', 'card_brand', 'card_exp_month', 'card_exp_year')
        }),
        ('Billing Info', {
            'fields': ('billing_email', 'billing_name')
        }),
        ('Stripe', {
            'fields': ('stripe_payment_method_id',)
        }),
    )

@admin.register(UsageRecord)
class UsageRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'usage_type', 'quantity', 'job', 'created_at')
    list_filter = ('usage_type',)
    search_fields = ('user__email', 'job__id')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Usage Info', {
            'fields': ('user', 'subscription', 'usage_type', 'quantity')
        }),
        ('Reference', {
            'fields': ('job', 'metadata')
        }),
    )
