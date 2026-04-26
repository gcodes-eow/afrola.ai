# backend/pricing/urls.py

from django.urls import path
from . import views

app_name = 'pricing'

urlpatterns = [
    path('', views.pricing_index, name='index'),
]