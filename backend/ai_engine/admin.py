# backend/ai_engine/admin.py

from django.contrib import admin
from .models import AIModel, ProcessingTask, LanguagePair, ProcessingQueue, ProcessingLog, BatchProcessingJob

@admin.register(AIModel)
class AIModelAdmin(admin.ModelAdmin):
    list_display = ('name', 'version', 'model_type', 'status', 'created_at')
    list_filter = ('model_type', 'status')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(ProcessingTask)
class ProcessingTaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'job', 'task_type', 'status', 'processing_time', 'created_at')
    list_filter = ('task_type', 'status')
    search_fields = ('job__id', 'error_message')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(LanguagePair)
class LanguagePairAdmin(admin.ModelAdmin):
    list_display = ('source_language', 'target_language', 'is_active', 'bleu_score')
    list_filter = ('is_active', 'source_language')
    search_fields = ('source_language', 'target_language')

@admin.register(ProcessingQueue)
class ProcessingQueueAdmin(admin.ModelAdmin):
    list_display = ('job', 'priority', 'position', 'queued_at')
    list_filter = ('priority',)
    search_fields = ('job__id',)

@admin.register(ProcessingLog)
class ProcessingLogAdmin(admin.ModelAdmin):
    list_display = ('level', 'message', 'created_at')
    list_filter = ('level',)
    search_fields = ('message',)
    readonly_fields = ('created_at',)

@admin.register(BatchProcessingJob)
class BatchProcessingJobAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'status', 'completed_jobs', 'total_jobs', 'created_at')
    list_filter = ('status',)
    search_fields = ('name', 'user__email')
