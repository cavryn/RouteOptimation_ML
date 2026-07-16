"""
Evaluator Module
Menghitung metrik evaluasi sesuai Tabel IV
"""

import numpy as np
import pandas as pd
from typing import Dict, List


class RouteEvaluator:
    """Evaluasi kualitas rute"""
    
    def evaluate_route(self, route: List[int], distance_matrix: np.ndarray,
                       constraints_df: pd.DataFrame) -> Dict:
        """Evaluasi lengkap route"""
        total_distance = self._calculate_total_distance(route, distance_matrix)
        tw_violations = self._count_time_window_violations(route, distance_matrix, constraints_df)
        feasibility = self._calculate_route_feasibility(route, constraints_df)
        
        nodes_visited = len([n for n in route if n != 0])
        total_nodes = len(constraints_df) - 1
        
        return {
            'total_distance_km': round(total_distance, 2),
            'time_window_violations': tw_violations,
            'route_feasibility_pct': round(feasibility * 100, 2),
            'nodes_visited': nodes_visited,
            'total_nodes': total_nodes,
            'visit_rate_pct': round((nodes_visited / total_nodes * 100) if total_nodes > 0 else 0, 2)
        }
    
    def _calculate_total_distance(self, route: List[int], distance_matrix: np.ndarray) -> float:
        """Calculate total route distance"""
        total = 0.0
        for i in range(len(route) - 1):
            total += distance_matrix[route[i]][route[i+1]]
        if len(route) > 0:
            total += distance_matrix[route[-1]][route[0]]
        return total
    
    def _count_time_window_violations(self, route: List[int], distance_matrix: np.ndarray,
                                      constraints_df: pd.DataFrame) -> int:
        """Count time window violations"""
        violations = 0
        current_time = 0
        
        for i, node_id in enumerate(route):
            if node_id == 0:
                continue
            if node_id >= len(constraints_df):
                continue
            
            node_data = constraints_df.iloc[node_id]
            
            if i > 0:
                prev_node = route[i-1]
                travel_time = distance_matrix[prev_node][node_id] * 2
                current_time += travel_time
            
            tw_open = node_data.get('tw_open_min', 0)
            tw_close = node_data.get('tw_close_min', 1440)
            
            if current_time > tw_close:
                violations += 1
            elif current_time < tw_open:
                current_time = tw_open
            
            service_time = node_data.get('service_time', 5)
            current_time += service_time
        
        return violations
    
    def _calculate_route_feasibility(self, route: List[int], constraints_df: pd.DataFrame) -> float:
        """Calculate route feasibility percentage"""
        if len(route) <= 1:
            return 0.0
        
        total_checks = 0
        passed_checks = 0
        
        for node_id in route:
            if node_id == 0:
                continue
            if node_id >= len(constraints_df):
                continue
            
            node_data = constraints_df.iloc[node_id]
            total_checks += 1
            if node_data.get('road_status', True):
                passed_checks += 1
        
        return passed_checks / total_checks if total_checks > 0 else 0.0
    
    def compare_algorithms(self, aco_route: List[int], baseline_route: List[int],
                          distance_matrix: np.ndarray, constraints_df: pd.DataFrame) -> Dict:
        """Compare ACO vs baseline"""
        aco_eval = self.evaluate_route(aco_route, distance_matrix, constraints_df)
        baseline_eval = self.evaluate_route(baseline_route, distance_matrix, constraints_df)
        
        distance_improvement = baseline_eval['total_distance_km'] - aco_eval['total_distance_km']
        improvement_pct = (distance_improvement / baseline_eval['total_distance_km'] * 100) if baseline_eval['total_distance_km'] > 0 else 0
        
        return {
            'aco': aco_eval,
            'baseline': baseline_eval,
            'improvement_km': round(distance_improvement, 2),
            'improvement_pct': round(improvement_pct, 2),
            'aco_better': distance_improvement > 0
        }
