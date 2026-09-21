import requests

BASE = "http://localhost:5000/api"

# Health
r = requests.get(f"{BASE}/health")
print("HEALTH:", r.status_code, r.text)

# Register
import time
email = f"pytest{int(time.time())}@x.com"
r = requests.post(f"{BASE}/auth/register", json={
    "name": "PyTest",
    "email": email,
    "password": "secret123",
    "role": "PASSENGER",
})
print("REGISTER:", r.status_code, r.text)

# Login
r = requests.post(f"{BASE}/auth/login", json={
    "email": email,
    "password": "secret123",
})
print("LOGIN:", r.status_code, r.text)