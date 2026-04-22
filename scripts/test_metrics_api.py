import requests
import json

BASE_URL = "http://localhost:8000"

def test_metrics_api():
    print("1. Testing /api/metrics/health/oracle...")
    resp = requests.get(f"{BASE_URL}/api/metrics/health/oracle")
    print(json.dumps(resp.json(), indent=2))

    print("\n2. Testing /api/metrics/performance...")
    resp = requests.get(f"{BASE_URL}/api/metrics/performance")
    print(json.dumps(resp.json(), indent=2))

    print("\n3. Testing /api/metrics/partitions/summary...")
    resp = requests.get(f"{BASE_URL}/api/metrics/partitions/summary")
    print(json.dumps(resp.json(), indent=2))

    print("\n4. Testing /api/metrics/audit...")
    resp = requests.get(f"{BASE_URL}/api/metrics/audit")
    print(json.dumps(resp.json(), indent=2))

if __name__ == "__main__":
    test_metrics_api()
