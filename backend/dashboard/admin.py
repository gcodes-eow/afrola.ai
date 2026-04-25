# backend/dashboard/admin.py
from django.contrib import admin
from .models import UserDashboard, SavedItem, RecentActivity, UserAnalytics, DashboardWidget

@admin.register(UserDashboard)
class UserDashboardAdmin(admin.ModelAdmin):
    list_display = ('user', 'default_view', 'theme', 'updated_at')
    list_filter = ('default_view', 'theme')
    search_fields = ('user__email',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(SavedItem)
class SavedItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'item_type', 'created_at')
    list_filter = ('item_type',)
    search_fields = ('user__email', 'name')
    readonly_fields = ('created_at',)

@admin.register(RecentActivity)
class RecentActivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'activity_type', 'description', 'created_at')
    list_filter = ('activity_type',)
    search_fields = ('user__email', 'description')
    readonly_fields = ('created_at',)

@admin.register(UserAnalytics)
class UserAnalyticsAdmin(admin.ModelAdmin):
    list_display = ('user', 'total_transcriptions', 'total_translations', 'total_files_uploaded')
    search_fields = ('user__email',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(DashboardWidget)
class DashboardWidgetAdmin(admin.ModelAdmin):
    list_display = ('user', 'widget_type', 'title', 'column', 'order', 'is_visible')
    list_filter = ('widget_type', 'is_visible')
    search_fields = ('user__email', 'title')
