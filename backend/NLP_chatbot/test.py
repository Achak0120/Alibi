import requests, os

API_KEY = os.getenv("GOOGLE_API_KEY")

url = f"https://generativelanguage.googleapis.com/v1/models?key={API_KEY}"
resp = requests.get(url)
print(resp.status_code)
print(resp.json())
