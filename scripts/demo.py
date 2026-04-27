"""Automated demo script for the Gen-DBA system presentation."""
import time
import httpx
import json
import sys

API_BASE = "http://localhost:8000"


def demo_step(title, description):
    """Display the demo step title and pause."""
    print(f"\n{'='*60}")
    print(f"DEMO: {title}")
    print(f"  {description}")
    print(f"{'='*60}")
    input("Press Enter to continue...")


def main():
    print("\n" + "="*60)
    print("   Gen-DBA: AI-Driven Data Partitioning Agent")
    print("   Live Demonstration")
    print("="*60)

    try:
        # Step 1: Check System Health
        demo_step("System Check", "Verify connection to Oracle DB and FastAPI")
        r = httpx.get(f"{API_BASE}/api/metrics/health/oracle", timeout=10)
        print(f"  Oracle Status: {r.json()}")

        # Step 2: Show Current State
        demo_step("Current State", "Show the existing partition layout")
        r = httpx.get(f"{API_BASE}/api/partitions/current", timeout=10)
        partitions = r.json()["partitions"]
        print(f"  Current partitions: {len(partitions)}")
        if not partitions:
            print("  => No partitions found (baseline state)")
        else:
            print("  => Existing partitions will be analyzed.")

        # Step 3: Trigger Agent Analysis
        demo_step("Agent Analysis", "Trigger AI to analyze workload and recommend partitions")
        print("  Sending request to Agent... (This might take a minute)")
        r = httpx.post(f"{API_BASE}/api/agent/analyze", timeout=120)
        result = r.json()
        run_id = result.get("run_id")
        
        if not run_id:
             print(f"  Failed to get run_id. Response: {result}")
             sys.exit(1)

        print(f"  Session ID: {run_id}")
        print(f"  Phase: {result.get('phase')}")
        
        recs = result.get("recommendations", [])
        print(f"  Recommendations: {len(recs)}")

        for i, rec in enumerate(recs):
            print(f"\n  Recommendation {i+1}:")
            print(f"    Table: {rec.get('target_table')}")
            print(f"    Strategy: {rec.get('strategy')} on {rec.get('partition_key')}")
            print(f"    Risk: {rec.get('risk_level')}")
            print(f"    Reasoning: {rec.get('reasoning')[:200]}...")
            print(f"    DDL: {rec.get('ddl_script')[:200]}...")

        # Step 4: Human Approval
        demo_step("Human Approval", "DBA reviews and approves the AI recommendations")
        r = httpx.post(
            f"{API_BASE}/api/partitions/approve/{run_id}",
            json={"approved": True, "notes": "Approved for live demo"},
            timeout=10
        )
        print(f"  Approval status: {r.json()}")

        # Step 5: Execution
        demo_step("Execution", "Apply the approved partition changes to Oracle")
        print("  Executing DDL... (This will take some time depending on data size)")
        r = httpx.post(f"{API_BASE}/api/agent/execute/{run_id}", timeout=300)
        result = r.json()
        print(f"  Phase: {result.get('phase')}")
        for er in result.get("execution_results", []):
            status = 'SUCCESS' if er.get('success') else 'FAILED'
            print(f"  {er.get('table', 'N/A')}: {status}")

        # Step 6: Post-Execution State
        demo_step("Final State", "Show the updated partition layout")
        r = httpx.get(f"{API_BASE}/api/partitions/current", timeout=10)
        partitions = r.json()["partitions"]
        print(f"  Partitions after Gen-DBA: {len(partitions)}")
        for p in partitions[:10]:
            print(f"    {p}")

        if len(partitions) > 10:
             print(f"    ... and {len(partitions) - 10} more.")

        print("\n" + "="*60)
        print("   Demo Complete!")
        print("="*60)

    except httpx.ConnectError:
        print("\n  ERROR: Connection to API failed. Is the FastAPI server running?")
        print("  Run 'python -m uvicorn app.main:app' first.")
    except Exception as e:
        print(f"\n  ERROR: An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
