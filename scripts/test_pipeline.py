import requests
import time
import json

BASE_URL = "http://localhost:8000"

def test_pipeline():
    print("1. Checking Server Health...")
    resp = requests.get(f"{BASE_URL}/health")
    print(resp.json())

    print("\n2. Triggering Analysis (This will call OpenAI)...")
    start_time = time.time()
    resp = requests.post(f"{BASE_URL}/api/agent/analyze")
    data = resp.json()
    print(json.dumps(data, indent=2))
    run_id = data.get("run_id")
    
    if not run_id:
        print("Analysis failed.")
        return

    print(f"\nTime taken for reasoning: {time.time() - start_time:.1f} seconds")

    print("\n3. Checking Pending Approvals...")
    resp = requests.get(f"{BASE_URL}/api/partitions/pending")
    print(json.dumps(resp.json(), indent=2))

    print(f"\n4. Approving run_id {run_id}...")
    resp = requests.post(
        f"{BASE_URL}/api/partitions/approve/{run_id}",
        json={"approved": True, "notes": "Approved by automated test"}
    )
    print(json.dumps(resp.json(), indent=2))

    print(f"\n5. Executing DDL and Evaluating...")
    resp = requests.post(f"{BASE_URL}/api/agent/execute/{run_id}")
    print(json.dumps(resp.json(), indent=2))

    print("\n6. Checking Final Status...")
    resp = requests.get(f"{BASE_URL}/api/agent/status/{run_id}")
    print(json.dumps(resp.json(), indent=2))

if __name__ == "__main__":
    time.sleep(2)  # Give server a moment to start fully
    test_pipeline()
