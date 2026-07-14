"""
PSO Optimizer Module
Particle Swarm Optimization untuk route optimization
"""

import numpy as np
import pandas as pd
from typing import Tuple, Dict, List
from mealpy import FloatVar
from mealpy.swarm_based.PSO import OriginalPSO


class RouteOptimizationProblem:
    """Custom Problem untuk MealPy PSO"""
    
    def __init__(self, distance_matrix: np.ndarray, constraints_df: pd.DataFrame, 
                 time_window_penalty: float = 1000.0):
        self.distance_matrix = distance_matrix
        self.constraints_df = constraints_df
        self.time_window_penalty = time_window_penalty
        self.n_nodes = distance_matrix.shape[0]
        
        # Define bounds for PSO
        self.lb = [0.0] * (self.n_nodes - 1)
        self.ub = [1.0] * (self.n_nodes - 1)
        self.bounds = FloatVar(lb=self.lb, ub=self.ub)
    
    def fitness_function(self, solution):
        """Fitness function: minimize total distance + penalties"""
        route = self._decode_solution(solution)
        total_distance = 0.0
        
        for i in range(len(route) - 1):
            total_distance += self.distance_matrix[route[i]][route[i+1]]
        
        # Return to depot
        total_distance += self.distance_matrix[route[-1]][route[0]]
        
        # Add time window penalty
        penalty = self._calculate_time_window_penalty(route)
        
        return total_distance + penalty
    
    def _decode_solution(self, solution: np.ndarray) -> List[int]:
        """Decode continuous solution to discrete route"""
        route = [0]  # Start from depot
        
        # Sort nodes by solution values
        node_values = [(i+1, solution[i]) for i in range(len(solution))]
        sorted_nodes = sorted(node_values, key=lambda x: x[1])
        
        # Build route excluding closed roads
        for node_id, _ in sorted_nodes:
            if node_id < len(self.constraints_df):
                if self.constraints_df.iloc[node_id].get('road_status', True):
                    route.append(node_id)
            else:
                route.append(node_id)
        
        return route
    
    def _calculate_time_window_penalty(self, route: List[int]) -> float:
        """Calculate penalty for time window violations"""
        penalty = 0.0
        current_time = 0
        
        for i, node_id in enumerate(route):
            if node_id == 0:
                continue
            
            if node_id >= len(self.constraints_df):
                continue
            
            node_data = self.constraints_df.iloc[node_id]
            
            # Travel time
            if i > 0:
                prev_node = route[i-1]
                travel_time = self.distance_matrix[prev_node][node_id] * 2
                current_time += travel_time
            
            # Check time window
            tw_open = node_data.get('tw_open_min', 0)
            tw_close = node_data.get('tw_close_min', 1440)
            
            if current_time < tw_open:
                current_time = tw_open
            elif current_time > tw_close:
                penalty += self.time_window_penalty
            
            # Service time
            service_time = node_data.get('service_time', 5)
            current_time += service_time
        
        return penalty


class PSOOptimizer:
    """PSO Optimizer wrapper"""
    
    def __init__(self, n_particles: int = 20, n_iterations: int = 200):
        self.n_particles = n_particles
        self.n_iterations = n_iterations
        self.best_route = None
        self.best_distance = None
        self.convergence_curve = []
    
    def optimize(self, distance_matrix: np.ndarray, 
                 constraints_df: pd.DataFrame) -> Tuple[List[int], float, List[float]]:
        """Run PSO optimization"""
        
        problem = RouteOptimizationProblem(distance_matrix, constraints_df)
        
        # Create PSO model
        model = OriginalPSO(epoch=self.n_iterations, pop_size=self.n_particles)
        
        # Solve problem
        best_position, best_fitness = model.solve(problem)
        
        # Decode result
        self.best_route = problem._decode_solution(best_position)
        self.best_distance = best_fitness
        self.convergence_curve = model.history.list_global_best_fit
        
        return self.best_route, self.best_distance, self.convergence_curve
    
    def get_route_details(self) -> Dict:
        """Get route details"""
        if self.best_route is None:
            return {}
        
        return {
            'algorithm': 'PSO (Particle Swarm Optimization)',
            'route': self.best_route,
            'total_distance_km': self.best_distance,
            'nodes_visited': len(self.best_route) - 1,
            'parameters': {
                'n_particles': self.n_particles,
                'n_iterations': self.n_iterations
            }
        }
