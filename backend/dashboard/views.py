# backend/dashboard/views.py

from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def index(request):
    """Dashboard home page"""
    recent_jobs = request.user.jobs.all().order_by('-created_at')[:5]

    context = {
        'recent_jobs': recent_jobs,
        'total_jobs': request.user.jobs.count(),
        'completed_jobs': request.user.jobs.filter(status='completed').count(),
        'processing_jobs': request.user.jobs.filter(status__in=['pending', 'queued', 'processing']).count(),
    }
    return render(request, 'dashboard/index.html', context)