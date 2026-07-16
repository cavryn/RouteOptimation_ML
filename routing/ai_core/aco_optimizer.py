"""
ACO Optimizer Module
Ant Colony Optimization untuk route optimization menggunakan DSTSP
Sesuai dengan parameter Tabel III paper UTS
"""

import numpy as np
import pandas as pd
from typing import Tuple, Dict, List
from mealpy import FloatVar
from mealpy.swarm_based.ACOR import OriginalACOR


class RouteOptimizationProblem:
    """Custom Problem untuk MealPy ACO"""
    
    def __init__(self, distance_matrix: np.ndarray, constraints_df: pd.DataFrame, 
                 time_window_penalty: float = 1000.0):
        self.distance_matrix = distance_matrix
        self.constraints_df = constraints_df
        self.time_window_penalty = time_window_penalty
        self.n_nodes = distance_matrix.shape[0]
        
        # Define bounds for ACO
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
        
        # Sort nodes by solution values (pheromone-based ordering)
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


class ACOOptimizer:
    """ACO Optimizer wrapper menggunakan parameter dari Tabel III paper"""
    
    def __init__(self, n_ants: int = 20, n_iterations: int = 200, 
                 alpha: float = 1.0, beta: float = 2.0, 
                 rho: float = 0.5, Q: float = 100.0):
        """
        Initialize ACO optimizer dengan parameter sesuai paper UTS
        
        Parameters:
        -----------
        n_ants : int
            Jumlah semut (population size), default 20
        n_iterations : int
            Jumlah iterasi maksimum, default 200
        alpha : float
            Bobot pheromone (α), default 1.0
        beta : float
            Bobot heuristic information (β), default 2.0
        rho : float
            Evaporation rate (ρ), default 0.5
        Q : float
            Pheromone constant, default 100.0
        """
        self.n_ants = n_ants
        self.n_iterations = n_iterations
        self.alpha = alpha
        self.beta = beta
        self.rho = rho
        self.Q = Q
        self.best_route = None
        self.best_distance = None
        self.convergence_curve = []
    
    def optimize(self, distance_matrix: np.ndarray, 
                 constraints_df: pd.DataFrame) -> Tuple[List[int], float, List[float]]:
        """Run ACO optimization"""
        
        # Create problem definition as dict for MealPy
        problem_dict = {
            "obj_func": self._create_fitness_function(distance_matrix, constraints_df),
            "bounds": FloatVar(lb=[0.0] * (distance_matrix.shape[0] - 1), 
                              ub=[1.0] * (distance_matrix.shape[0] - 1)),
            "minmax": "min",
        }
        
        # Create ACO model with parameters from paper
        model = OriginalACOR(
            epoch=self.n_iterations, 
            pop_size=self.n_ants
        )
        
        # Solve problem
        g_best = model.solve(problem_dict)
        
        # Decode result
        self.best_route = self._decode_solution(g_best.solution, distance_matrix.shape[0], constraints_df)
        self.best_distance = g_best.target.fitness
        self.convergence_curve = model.history.list_global_best_fit
        
        return self.best_route, self.best_distance, self.convergence_curve
    
    def _create_fitness_function(self, distance_matrix: np.ndarray, constraints_df: pd.DataFrame):
        """Create fitness function closure"""
        def fitness_func(solution):
            route = self._decode_solution(solution, distance_matrix.shape[0], constraints_df)
            total_distance = 0.0
            
            for i in range(len(route) - 1):
                total_distance += distance_matrix[route[i]][route[i+1]]
            
            # Return to depot
            total_distance += distance_matrix[route[-1]][route[0]]
            
            # Add time window penalty
            penalty = self._calculate_time_window_penalty(route, distance_matrix, constraints_df)
            
            return total_distance + penalty
        
        return fitness_func
    
    def _decode_solution(self, solution: np.ndarray, n_nodes: int, constraints_df: pd.DataFrame) -> List[int]:
        """Decode continuous solution to discrete route"""
        route = [0]  # Start from depot
        
        # Sort nodes by solution values (pheromone-based ordering)
        node_values = [(i+1, solution[i]) for i in range(len(solution))]
        sorted_nodes = sorted(node_values, key=lambda x: x[1])
        
        # Build route excluding closed roads
        for node_id, _ in sorted_nodes:
            if node_id < len(constraints_df):
                if constraints_df.iloc[node_id].get('road_status', True):
                    route.append(node_id)
            else:
                route.append(node_id)
        
        return route
    
    def _calculate_time_window_penalty(self, route: List[int], distance_matrix: np.ndarray, 
                                       constraints_df: pd.DataFrame) -> float:
        """Calculate penalty for time window violations"""
        penalty = 0.0
        current_time = 0
        time_window_penalty = 1000.0
        
        for i, node_id in enumerate(route):
            if node_id == 0:
                continue
            
            if node_id >= len(constraints_df):
                continue
            
            node_data = constraints_df.iloc[node_id]
            
            # Travel time
            if i > 0:
                prev_node = route[i-1]
                travel_time = distance_matrix[prev_node][node_id] * 2
                current_time += travel_time
            
            # Check time window
            tw_open = node_data.get('tw_open_min', 0)
            tw_close = node_data.get('tw_close_min', 1440)
            
            if current_time < tw_open:
                current_time = tw_open
            elif current_time > tw_close:
                penalty += time_window_penalty
            
            # Service time
            service_time = node_data.get('service_time', 5)
            current_time += service_time
        
        return penalty

    def get_route_details(self) -> Dict:
        """Get route details"""
        if self.best_route is None:
            return {}
        
        return {
            'algorithm': 'ACO (Ant Colony Optimization)',
            'route': self.best_route,
            'total_distance_km': self.best_distance,
            'nodes_visited': len(self.best_route) - 1,
            'parameters': {
                'n_ants': self.n_ants,
                'n_iterations': self.n_iterations,
                'alpha': self.alpha,
                'beta': self.beta,
                'rho': self.rho,
                'Q': self.Q
            }
        }
