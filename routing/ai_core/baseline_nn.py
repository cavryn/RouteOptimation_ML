"""
Baseline Nearest Neighbor Algorithm
Greedy baseline untuk comparison
"""

import numpy as np
import pandas as pd
from typing import List, Tuple


class NearestNeighborBaseline:
    """Greedy Nearest Neighbor untuk baseline comparison"""
    
    def __init__(self):
        self.route = None
        self.total_distance = None
    
    def solve(self, distance_matrix: np.ndarray, 
              constraints_df: pd.DataFrame = None, 
              start_node: int = 0) -> Tuple[List[int], float]:
        """Solve TSP dengan Greedy Nearest Neighbor"""
        n_nodes = distance_matrix.shape[0]
        unvisited = set(range(n_nodes))
        current_node = start_node
        route = [current_node]
        unvisited.remove(current_node)
        total_distance = 0.0
        
        while unvisited:
            nearest_node = None
            min_distance = float('inf')
            
            for node in unvisited:
                # Check road status constraint
                if constraints_df is not None:
                    if node < len(constraints_df):
                        if not constraints_df.iloc[node].get('road_status', True):
                            continue
                
                distance = distance_matrix[current_node][node]
                
                if distance < min_distance:
                    min_distance = distance
                    nearest_node = node
            
            if nearest_node is None:
                break
            
            route.append(nearest_node)
            unvisited.remove(nearest_node)
            total_distance += min_distance
            current_node = nearest_node
        
        # Return to depot
        if len(route) > 1:
            total_distance += distance_matrix[current_node][start_node]
            route.append(start_node)
        
        self.route = route
        self.total_distance = total_distance
        
        return route, total_distance
    
    def get_route_details(self) -> dict:
        """Get route details"""
        if self.route is None:
            return {}
        
        return {
            'algorithm': 'Greedy Nearest Neighbor',
            'route': self.route,
            'total_distance_km': self.total_distance,
            'nodes_visited': len(self.route) - 1
        }
