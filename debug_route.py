import requests, os, django
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
django.setup()
from routing.models import DeliveryPoint
from dotenv import load_dotenv
load_dotenv()

api_key = os.environ.get('TOMTOM_API_KEY')
points = list(DeliveryPoint.objects.all())
print('Count:', len(points))

# Find the point that is furthest WEST (smallest longitude)
p_west = min(points, key=lambda x: x.longitude)
p_north = max(points, key=lambda x: x.latitude)
print(f'Westernmost: lat={p_west.latitude:.4f}, lon={p_west.longitude:.4f}')
print(f'Northernmost: lat={p_north.latitude:.4f}, lon={p_north.longitude:.4f}')
print(f'Depot: lat=-7.16434, lon=112.65168')
print(f'West delta from depot: {112.65168 - p_west.longitude:.4f} deg = ~{(112.65168 - p_west.longitude)*111:.1f} km')

# Test: depot -> westernmost point, what does the route look like?
url = f'https://api.tomtom.com/routing/1/calculateRoute/-7.16434,112.65168:{p_west.latitude},{p_west.longitude}/json'
params = [('key', api_key), ('travelMode', 'motorcycle'), ('routeType', 'fastest'),
          ('avoid', 'tollRoads'), ('avoid', 'motorways'), ('avoid', 'ferries')]
r = requests.get(url, params=params)
print('Status:', r.status_code)
if r.status_code == 200:
    data = r.json()
    pts = data['routes'][0]['legs'][0]['points']
    max_lat = max(p2['latitude'] for p2 in pts)
    min_lat = min(p2['latitude'] for p2 in pts)
    dist = data['routes'][0]['summary']['lengthInMeters']
    print(f'Route points: {len(pts)}')
    print(f'Lat range: {min_lat:.4f} to {max_lat:.4f}')
    print(f'Distance: {dist}m')
    print(f'NOTE: depot lat is -7.16434, delivery lat is {p_west.latitude:.4f}')
    print(f'Max lat in route = {max_lat:.4f} -> goes NORTH of delivery point!')
else:
    print('Error:', r.text[:300])
