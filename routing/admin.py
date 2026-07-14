"""
Admin configuration for routing app
"""

from django.contrib import admin
from .models import DeliveryPoint, OptimizationRun, ComparisonResult


@admin.register(DeliveryPoint)
class DeliveryPointAdmin(admin.ModelAdmin):
    list_display = ['node_id', 'latitude', 'longitude', 'demand', 'priority', 'road_status', 'created_at']
    list_filter = ['priority', 'road_status']
    search_fields = ['node_id']


@admin.register(OptimizationRun)
class OptimizationRunAdmin(admin.ModelAdmin):
    list_display = ['algorithm', 'n_nodes', 'total_distance_km', 'computation_time_sec', 'created_at']
    list_filter = ['algorithm', 'created_at']
    search_fields = ['notes']
    readonly_fields = ['created_at']


@admin.register(ComparisonResult)
class ComparisonResultAdmin(admin.ModelAdmin):
    list_display = ['pso_distance_km', 'baseline_distance_km', 'improvement_pct', 'pso_better', 'created_at']
    list_filter = ['pso_better', 'created_at']
    readonly_fields = ['created_at']
