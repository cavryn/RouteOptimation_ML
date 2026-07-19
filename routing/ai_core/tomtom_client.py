import requests
import numpy as np
from typing import List, Tuple, Optional, Dict
from django.conf import settings


class TomTomClient:
    """Client untuk berkomunikasi dengan TomTom API"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or getattr(settings, 'TOMTOM_API_KEY', None)
        self.base_url = "https://api.tomtom.com/routing"
    
    def get_distance_matrix(
        self, 
        coordinates: List[Tuple[float, float]],
        use_euclidean_fallback: bool = True
    ) -> Optional[np.ndarray]:
        """
        Get travel time matrix dari TomTom Matrix API v2
        coordinates format: [(lon, lat), ...]
        Returns matrix of travel times in MINUTES.
        """
        if not self.api_key:
            if use_euclidean_fallback:
                return self._calculate_euclidean_matrix(coordinates)
            return None

        try:
            url = f"{self.base_url}/matrix/2?key={self.api_key}"
            
            # TomTom expects point: { latitude, longitude }
            points = [{"point": {"latitude": lat, "longitude": lon}} for lon, lat in coordinates]
            
            payload = {
                "origins": points,
                "destinations": points,
                "options": {
                    "departAt": "now",  # Current time for live traffic
                    "traffic": True,
                    "routeType": "fastest"
                }
            }
            
            response = requests.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if 'matrix' in data:
                    n = len(coordinates)
                    matrix = np.zeros((n, n))
                    for i in range(n):
                        for j in range(n):
                            if i == j:
                                matrix[i][j] = 0.0
                            else:
                                cell = data['matrix'][i][j]
                                if 'routeSummary' in cell:
                                    # Use travel time in seconds, convert to minutes
                                    time_sec = cell['routeSummary'].get('travelTimeInSeconds', 0)
                                    matrix[i][j] = time_sec / 60.0
                                else:
                                    # Fallback for unreachable cells
                                    matrix[i][j] = 999999.0
                    return matrix
            
            print(f"TomTom Matrix API error: {response.text}")
            if use_euclidean_fallback:
                return self._calculate_euclidean_matrix(coordinates)
        except Exception as e:
            print(f"TomTom Matrix API exception: {e}")
            if use_euclidean_fallback:
                return self._calculate_euclidean_matrix(coordinates)
        return None
    
    def get_route_geometry(
        self, 
        coordinates: List[Tuple[float, float]]
    ) -> Optional[List[Tuple[float, float]]]:
        """
        Get actual road route geometry from TomTom Routing API
        coordinates format: [(lon, lat), ...]
        Returns list of (lat, lon) for Folium
        """
        if not self.api_key:
            return None

        try:
            # TomTom expects lat,lon:lat,lon:lat,lon...
            coords_str = ':'.join([f"{lat},{lon}" for lon, lat in coordinates])
            url = f"{self.base_url}/1/calculateRoute/{coords_str}/json"
            
            params = {
                'key': self.api_key,
                'departAt': 'now',
                'traffic': 'true',
                'routeType': 'fastest'
            }
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if 'routes' in data and len(data['routes']) > 0:
                    route_points = []
                    legs = data['routes'][0].get('legs', [])
                    for leg in legs:
                        points = leg.get('points', [])
                        for p in points:
                            # Folium expects [lat, lon]
                            route_points.append([p['latitude'], p['longitude']])
                    return route_points
            else:
                print(f"TomTom Routing API error: {response.text}")
        except Exception as e:
            print(f"TomTom Routing API exception: {e}")
        return None

    def _calculate_euclidean_matrix(self, coordinates: List[Tuple[float, float]]) -> np.ndarray:
        """Fallback: Euclidean distance matrix (in pseudo-minutes)"""
        n = len(coordinates)
        matrix = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                if i != j:
                    lon1, lat1 = coordinates[i]
                    lon2, lat2 = coordinates[j]
                    distance_km = self._haversine_distance(lat1, lon1, lat2, lon2)
                    # Assume average speed of 30 km/h (0.5 km/minute)
                    matrix[i][j] = distance_km / 0.5
        return matrix
    
    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Haversine formula untuk distance calculation (returns km)"""
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
