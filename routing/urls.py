"""
URL Configuration for routing app
"""

from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('generate-sample/', views.generate_sample_data, name='generate_sample'),
    path('optimize/', views.run_optimization, name='run_optimization'),
    path('result/', views.result, name='result'),
    path('history/', views.history, name='history'),
]
