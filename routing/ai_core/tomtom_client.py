import requests
import numpy as np
from typing import List, Tuple, Optional
from django.conf import settings


class TomTomClient:
    """Client untuk berkomunikasi dengan TomTom API"""

    ROUTE_PARAMS = {
        'routeType': 'fastest',
        'travelMode': 'motorcycle',
        'avoid': 'tollRoads',
        'traffic': 'true',
        'departAt': 'now',
    }

    def __init__(self, api_key: str = None):
        self.api_key = api_key or getattr(settings, 'TOMTOM_API_KEY', None)
        self.base_url = "https://api.tomtom.com/routing"

    # ──────────────────────────────────────────────────────────────────────────
    # Public: travel-time matrix (n×n), units = MINUTES
    # ──────────────────────────────────────────────────────────────────────────
    def get_distance_matrix(
        self,
        coordinates: List[Tuple[float, float]],
        use_euclidean_fallback: bool = True,
    ) -> Optional[np.ndarray]:
        """
        Build a travel-time matrix using the TomTom Routing API (pairwise).
        coordinates format: [(lon, lat), ...]
        Returns ndarray of shape (n, n) in minutes.

        Menggunakan pairwise karena Matrix API v2 gratis hanya mendukung
        hingga 100 sel (10 × 10). Untuk n > 10 kita pakai cara batch pairwise
        dengan calculateRoute untuk setiap pasang (i→j).
        """
        if not self.api_key:
            return self._calculate_haversine_matrix(coordinates)

        n = len(coordinates)
        matrix = np.zeros((n, n))

        try:
            for i in range(n):
                for j in range(n):
                    if i == j:
                        matrix[i][j] = 0.0
                        continue
                    lon1, lat1 = coordinates[i]
                    lon2, lat2 = coordinates[j]
                    travel_min = self._get_pairwise_time(lat1, lon1, lat2, lon2)
                    if travel_min is None:
                        # Fallback cell: use haversine estimate @ 30 km/h
                        dist_km = self._haversine_distance(lat1, lon1, lat2, lon2)
                        travel_min = dist_km / 0.5  # 0.5 km/min = 30 km/h
                    matrix[i][j] = travel_min

            print(f"[TomTom] Distance matrix built: {n}×{n} (pairwise routing)")
            return matrix

        except Exception as e:
            print(f"[TomTom] Matrix build exception: {e}")
            if use_euclidean_fallback:
                return self._calculate_haversine_matrix(coordinates)
            return None

    # ──────────────────────────────────────────────────────────────────────────
    # Public: full route geometry for map drawing
    # ──────────────────────────────────────────────────────────────────────────
    def get_route_geometry(
        self,
        coordinates: List[Tuple[float, float]],
    ) -> Optional[List[Tuple[float, float]]]:
        """
        Get actual road route geometry from TomTom Routing API.
        coordinates format: [(lon, lat), ...]
        Returns list of [lat, lon] for Folium.
        """
        if not self.api_key or len(coordinates) < 2:
            return None

        try:
            coords_str = ':'.join([f"{lat},{lon}" for lon, lat in coordinates])
            url = f"{self.base_url}/1/calculateRoute/{coords_str}/json"
            params = dict(self.ROUTE_PARAMS)
            params['key'] = self.api_key

            response = requests.get(url, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                if 'routes' in data and data['routes']:
                    route_points = []
                    for leg in data['routes'][0].get('legs', []):
                        for p in leg.get('points', []):
                            route_points.append([p['latitude'], p['longitude']])
                    return route_points
            else:
                print(f"[TomTom] Routing API error {response.status_code}: {response.text[:200]}")
        except Exception as e:
            print(f"[TomTom] Routing API exception: {e}")
        return None

    # ──────────────────────────────────────────────────────────────────────────
    # Private helpers
    # ──────────────────────────────────────────────────────────────────────────
    def _get_pairwise_time(
        self, lat1: float, lon1: float, lat2: float, lon2: float
    ) -> Optional[float]:
        """Return travel time in MINUTES between two points via TomTom API."""
        try:
            url = f"{self.base_url}/1/calculateRoute/{lat1},{lon1}:{lat2},{lon2}/json"
            params = dict(self.ROUTE_PARAMS)
            params['key'] = self.api_key

            r = requests.get(url, params=params, timeout=15)
            if r.status_code == 200:
                data = r.json()
                if 'routes' in data and data['routes']:
                    time_sec = data['routes'][0]['summary'].get('travelTimeInSeconds', 0)
                    return time_sec / 60.0
        except Exception as e:
            print(f"[TomTom] Pairwise request exception: {e}")
        return None

    def _calculate_haversine_matrix(
        self, coordinates: List[Tuple[float, float]]
    ) -> np.ndarray:
        """Fallback: Haversine-based time estimate at 30 km/h (motorcycle on local roads)."""
        n = len(coordinates)
        matrix = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                if i != j:
                    lon1, lat1 = coordinates[i]
                    lon2, lat2 = coordinates[j]
                    dist_km = self._haversine_distance(lat1, lon1, lat2, lon2)
                    matrix[i][j] = dist_km / 0.5  # 30 km/h
        return matrix

    def _haversine_distance(
        self, lat1: float, lon1: float, lat2: float, lon2: float
    ) -> float:
        """Haversine formula — returns distance in km."""
        R = 6371.0
        φ1, φ2 = np.radians(lat1), np.radians(lat2)
        dφ = np.radians(lat2 - lat1)
        dλ = np.radians(lon2 - lon1)
        a = np.sin(dφ / 2) ** 2 + np.cos(φ1) * np.cos(φ2) * np.sin(dλ / 2) ** 2
        return R * 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
