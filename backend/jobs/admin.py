from django.contrib import admin
from .models import Job

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'job_type', 'status', 'created_at')
    list_filter = ('status', 'job_type')
    search_fields = ('user__email',)
