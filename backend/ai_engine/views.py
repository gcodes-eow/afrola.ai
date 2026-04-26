# backend/ai_engine/views.py
"""Task status API views for monitoring Celery tasks and job progress."""
from celery.result import AsyncResult
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.core.cache import cache
from jobs.models import Job


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def task_status(request, task_id):
    """Get Celery task status by task ID"""
    result = AsyncResult(task_id)
    response = {
        'task_id': task_id,
        'status': result.status,
        'ready': result.ready(),
    }

    if result.ready():
        if result.successful():
            response['result'] = result.result
        else:
            response['error'] = str(result.info) if result.info else 'Unknown error'
            response['traceback'] = result.traceback
    else:
        # Task still running — include progress info if available
        if result.info and isinstance(result.info, dict):
            response['progress'] = result.info

    return Response(response)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def job_progress(request, job_id):
    """Get real-time job progress from cache"""
    job = get_object_or_404(Job, id=job_id, user=request.user)

    progress = cache.get(f'job_progress_{job_id}', {
        'progress': _calculate_progress(job),
        'step': job.status,
        'updated_at': str(job.updated_at) if job.updated_at else None,
    })

    # Add job summary
    progress['job_id'] = str(job.id)
    progress['job_type'] = job.job_type
    progress['status'] = job.status
    progress['status_display'] = job.get_status_display()

    return Response(progress)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def retry_job(request, job_id):
    """Manually retry a failed job"""
    job = get_object_or_404(Job, id=job_id, user=request.user)

    if job.status != 'failed':
        return Response({'error': 'Only failed jobs can be retried'}, status=400)

    from ai_engine.utils import trigger_job_processing
    job.retry_count = 0
    job.status = 'pending'
    job.error_message = ''
    job.save()

    trigger_job_processing(job)

    return Response({
        'status': 'retrying',
        'job_id': str(job.id),
    })


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def cancel_job(request, job_id):
    """Cancel a pending or queued job"""
    job = get_object_or_404(Job, id=job_id, user=request.user)

    if job.status not in ('pending', 'queued'):
        return Response({'error': 'Only pending or queued jobs can be canceled'}, status=400)

    # If there's a Celery task, revoke it
    from ai_engine.models import ProcessingQueue
    try:
        queue_item = job.queue_item
        if queue_item.celery_task_id:
            from celery import current_app
            current_app.control.revoke(queue_item.celery_task_id, terminate=True)
    except ProcessingQueue.DoesNotExist:
        pass

    job.status = 'cancelled'
    job.save()
    cache.delete(f'job_progress_{job_id}')

    return Response({'status': 'cancelled', 'job_id': str(job.id)})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def worker_status(request):
    """Get Celery worker status (admin only)"""
    if not request.user.is_staff:
        return Response({'error': 'Staff access required'}, status=403)

    from celery import current_app
    inspect = current_app.control.inspect()

    return Response({
        'active': inspect.active() if inspect else {},
        'scheduled': inspect.scheduled() if inspect else {},
        'registered': inspect.registered() if inspect else {},
        'stats': inspect.stats() if inspect else {},
    })


def _calculate_progress(job):
    """Calculate job progress based on status"""
    progress_map = {
        'pending': 0,
        'queued': 5,
        'processing': 50,
        'completed': 100,
        'failed': 0,
        'cancelled': 0,
    }
    return progress_map.get(job.status, 0)
