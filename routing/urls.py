"""
URL Configuration for routing app
"""

from django.urls import path
from . import views

urlpatterns = [
    # Core pages
    path('', views.dashboard, name='dashboard'),
    path('optimasi-rute/', views.optimasi_rute, name='optimasi_rute'),
    path('data-paket/', views.data_paket, name='data_paket'),
    path('tambah-paket/', views.tambah_paket, name='tambah_paket'),
    path('live-map/', views.live_map, name='live_map'),
    path('statistik/', views.statistik, name='statistik'),
    path('pengaturan/', views.pengaturan, name='pengaturan'),

    # History & Result
    path('history/', views.history, name='history'),
    path('result/', views.result, name='result'),

    # Actions
    path('generate-sample/', views.generate_sample_data, name='generate_sample'),
    path('optimize/', views.run_optimization, name='run_optimization'),
]
