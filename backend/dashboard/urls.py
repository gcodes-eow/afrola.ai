# backend/dashboard/urls.py

from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.index, name='index'),
    path('upload/', views.upload_media, name='upload_media'),
    path('job/<uuid:job_id>/', views.job_detail, name='job_detail'),
    path('job/<uuid:job_id>/download/<str:output_type>/', views.download_result, name='download_result'),
]
