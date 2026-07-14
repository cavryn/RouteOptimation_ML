"""
OSRM Client Module
Wrapper untuk komunikasi dengan OSRM API
"""

import requests
import numpy as np
from typing import List, Tuple, Optional, Dict
import time


class OSRMClient:
    """Client untuk berkomunikasi dengan OSRM routing engine"""
    
    def __init__(self, base_url: str = "http://router.project-osrm.org"):
        self.base_url = base_url.rstrip('/')
        self.last_request_time = 0
        self.min_request_interval = 0.1
    
    def _rate_limit(self):
        """Rate limiting untuk avoid overload API"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)
        self.last_request_time = time.time()
    
    def get_distance_matrix(
        self, 
        coordinates: List[Tuple[float, float]],
        use_euclidean_fallback: bool = True
    ) -> Optional[np.ndarray]:
        """Get distance matrix dari OSRM API"""
        try:
            self._rate_limit()
            coords_str = ';'.join([f"{lon},{lat}" for lon, lat in coordinates])
            url = f"{self.base_url}/table/v1/driving/{coords_str}"
            params = {'annotations': 'distance'}
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if 'distances' in data:
                    return np.array(data['distances']) / 1000.0
            
            if use_euclidean_fallback:
                return self._calculate_euclidean_matrix(coordinates)
        except:
            if use_euclidean_fallback:
                return self._calculate_euclidean_matrix(coordinates)
        return None
    
    def _calculate_euclidean_matrix(self, coordinates: List[Tuple[float, float]]) -> np.ndarray:
        """Fallback: Euclidean distance matrix"""
        n = len(coordinates)
        matrix = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                if i != j:
                    lon1, lat1 = coordinates[i]
                    lon2, lat2 = coordinates[j]
                    distance = self._haversine_distance(lat1, lon1, lat2, lon2)
                    matrix[i][j] = distance
        return matrix
    
    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Haversine formula untuk distance calculation"""
        R = 6371.0
        lat1_rad = np.radians(lat1)
        lon1_rad = np.radians(lon1)
        lat2_rad = np.radians(lat2)
        lon2_rad = np.radians(lon2)
        
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = np.sin(dlat/2)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon/2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
        return R * c
    
    def test_connection(self) -> bool:
        """Test koneksi ke OSRM API"""
        try:
            test_coords = [(112.651680, -7.164340)]
            coords_str = f"{test_coords[0][0]},{test_coords[0][1]}"
            url = f"{self.base_url}/nearest/v1/driving/{coords_str}"
            response = requests.get(url, timeout=5)
            return response.status_code == 200
        except:
            return False
