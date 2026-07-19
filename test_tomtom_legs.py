import requests, os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from dotenv import load_dotenv
from routing.models import DeliveryPoint
load_dotenv()
api_key = os.environ.get('TOMTOM_API_KEY')
points = list(DeliveryPoint.objects.all()[:15])
coords_str = ':'.join([f'{p.latitude},{p.longitude}' for p in points])
url = f'https://api.tomtom.com/routing/1/calculateRoute/{coords_str}/json?key={api_key}&routeType=fastest'
r = requests.get(url)
print('Status:', r.status_code)
if r.status_code == 200:
    data = r.json()
    legs = data['routes'][0]['legs']
    for i, leg in enumerate(legs):
        pts = leg['points']
        dist = leg['summary']['lengthInMeters']
        print(f'Leg {i}: {len(pts)} points. Dist: {dist}')
