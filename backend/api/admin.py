# backend/api/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import (
    APIKey, APIRequestLog, WebhookEndpoint, WebhookDelivery,
    RateLimitRule, APIAccessLog, APIUsageSummary
)

@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'key_preview', 'is_active', 'last_used_at', 'total_requests', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'user__email', 'key_prefix')
    readonly_fields = ('key', 'key_prefix', 'total_requests', 'created_at')
    
    fieldsets = (
        ('Key Info', {
            'fields': ('name', 'user', 'key', 'key_prefix')
        }),
        ('Permissions', {
            'fields': ('permissions',)
        }),
        ('Rate Limiting', {
            'fields': ('rate_limit_per_minute', 'rate_limit_per_day')
        }),
        ('Status', {
            'fields': ('is_active', 'expires_at', 'last_used_at', 'total_requests')
        }),
    )
    
    def key_preview(self, obj):
        return format_html('<code>{}</code>', f"{obj.key_prefix}...")
    key_preview.short_description = 'API Key'

@admin.register(APIRequestLog)
class APIRequestLogAdmin(admin.ModelAdmin):
    list_display = ('method', 'path', 'status_code', 'user', 'response_time_ms', 'created_at')
    list_filter = ('method', 'status_code', 'created_at')
    search_fields = ('path', 'user__email', 'ip_address')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Request', {
            'fields': ('method', 'path', 'query_params', 'api_key', 'user')
        }),
        ('Response', {
            'fields': ('status_code', 'response_time_ms', 'error_message')
        }),
        ('Client Info', {
            'fields': ('ip_address', 'user_agent', 'rate_limit_remaining')
        }),
    )

@admin.register(WebhookEndpoint)
class WebhookEndpointAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'url_preview', 'is_active', 'failure_count', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'user__email', 'url')
    readonly_fields = ('secret', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Endpoint Info', {
            'fields': ('name', 'user', 'url', 'secret')
        }),
        ('Events', {
            'fields': ('events',)
        }),
        ('Status', {
            'fields': ('is_active', 'last_triggered_at', 'failure_count')
        }),
    )
    
    def url_preview(self, obj):
        return format_html('<a href="{}" target="_blank">{}</a>', obj.url, obj.url[:50])
    url_preview.short_description = 'URL'

@admin.register(WebhookDelivery)
class WebhookDeliveryAdmin(admin.ModelAdmin):
    list_display = ('webhook', 'event_type', 'status', 'attempt_count', 'delivered_at', 'created_at')
    list_filter = ('status', 'event_type', 'attempt_count')
    search_fields = ('webhook__name', 'webhook__user__email')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Delivery Info', {
            'fields': ('webhook', 'event_type', 'payload', 'status')
        }),
        ('Response', {
            'fields': ('response_status_code', 'response_body')
        }),
        ('Retry Info', {
            'fields': ('attempt_count', 'next_retry_at')
        }),
        ('Timing', {
            'fields': ('delivered_at',)
        }),
    )

@admin.register(RateLimitRule)
class RateLimitRuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'endpoint_pattern', 'method', 'requests', 'time_window', 'is_active', 'priority')
    list_filter = ('method', 'time_window', 'is_active')
    search_fields = ('name', 'endpoint_pattern')
    list_editable = ('requests', 'is_active', 'priority')
    
    fieldsets = (
        ('Rule Info', {
            'fields': ('name', 'endpoint_pattern', 'method')
        }),
        ('Rate Limits', {
            'fields': ('requests', 'time_window')
        }),
        ('Status', {
            'fields': ('is_active', 'priority')
        }),
    )

@admin.register(APIAccessLog)
class APIAccessLogAdmin(admin.ModelAdmin):
    list_display = ('request_log', 'db_query_count', 'db_query_time_ms', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('request_log__path', 'request_log__user__email')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Request/Response Headers', {
            'fields': ('request_headers', 'response_headers')
        }),
        ('Sizes', {
            'fields': ('request_size_bytes', 'response_size_bytes')
        }),
        ('Performance', {
            'fields': ('db_query_count', 'db_query_time_ms')
        }),
        ('Rate Limiting', {
            'fields': ('rate_limit_rule', 'rate_limit_reset_at')
        }),
    )

@admin.register(APIUsageSummary)
class APIUsageSummaryAdmin(admin.ModelAdmin):
    list_display = ('user', 'period_type', 'period_start', 'total_requests', 'successful_requests', 'failed_requests')
    list_filter = ('period_type', 'period_start')
    search_fields = ('user__email',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Period', {
            'fields': ('user', 'period_type', 'period_start', 'period_end')
        }),
        ('Usage Counts', {
            'fields': ('total_requests', 'successful_requests', 'failed_requests')
        }),
        ('Performance', {
            'fields': ('avg_response_time_ms', 'total_response_time_ms')
        }),
        ('Resources', {
            'fields': ('total_minutes_processed', 'total_bytes_transferred')
        }),
    )
 