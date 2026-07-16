"""
Django Models for Route Optimization System
Database schema untuk menyimpan delivery points dan optimization results
"""

from django.db import models
from django.utils import timezone
import json


class DeliveryPoint(models.Model):
    """Model untuk titik pengiriman"""
    node_id = models.IntegerField()
    latitude = models.FloatField()
    longitude = models.FloatField()
    demand = models.IntegerField(default=1)
    time_window_open = models.CharField(max_length=10, default='08:00')
    time_window_close = models.CharField(max_length=10, default='17:00')
    service_time = models.IntegerField(default=5, help_text="Service time in minutes")
    priority = models.IntegerField(default=2, choices=[(1, 'High'), (2, 'Medium'), (3, 'Low')])
    road_status = models.BooleanField(default=True, help_text="True if road is accessible")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['node_id']
    
    def __str__(self):
        return f"Node {self.node_id}"


class OptimizationRun(models.Model):
    """Model untuk menyimpan hasil optimization run"""
    algorithm = models.CharField(max_length=50, default='ACO')
    n_nodes = models.IntegerField()
    total_distance_km = models.FloatField()
    computation_time_sec = models.FloatField()
    time_window_violations = models.IntegerField(default=0)
    route_feasibility_pct = models.FloatField()
    
    # Parameters stored as JSON
    parameters = models.JSONField(default=dict)
    
    # Route stored as JSON array
    route_json = models.JSONField(default=list)
    
    # Notes/description
    notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.algorithm} Run - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    def get_parameters_display(self):
        """Get formatted parameters string"""
        if not self.parameters:
            return "N/A"
        return ", ".join([f"{k}={v}" for k, v in self.parameters.items()])


class ComparisonResult(models.Model):
    """Model untuk menyimpan hasil perbandingan algoritma"""
    aco_distance_km = models.FloatField()
    baseline_distance_km = models.FloatField()
    improvement_km = models.FloatField()
    improvement_pct = models.FloatField()
    aco_better = models.BooleanField()
    created_at = models.DateTimeField(default=timezone.now)
    
    # Link ke optimization run terkait
    optimization_run = models.ForeignKey(OptimizationRun, on_delete=models.CASCADE, 
                                        related_name='comparisons', null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Comparison - ACO: {self.aco_distance_km}km vs Baseline: {self.baseline_distance_km}km"
