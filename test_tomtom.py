import requests, os
from dotenv import load_dotenv
load_dotenv()
api_key = os.environ.get('TOMTOM_API_KEY')
print("Key exists:", bool(api_key))
url = f"https://api.tomtom.com/routing/1/calculateRoute/-7.16434,112.65168:-7.17,112.66/json?key={api_key}"
r = requests.get(url)
print(r.status_code)
print(str(r.json())[:500])
