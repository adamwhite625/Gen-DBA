"""Run benchmarks across all 3 scenarios: Baseline, Static Partition, Gen-DBA Optimized."""
import time
import json
import oracledb
from datetime import datetime

from app.config import settings
from scripts.benchmark import run_benchmark, save_results, compare_scenarios
from scripts.benchmark_queries import BENCHMARK_QUERIES


def get_connection():
    """Create a database connection using app settings."""
    return oracledb.connect(
        user=settings.ORACLE_USER,
        password=settings.ORACLE_PASSWORD,
        dsn=settings.ORACLE_DSN
    )


def execute_ddl(sql):
    """Execute a DDL statement and print status."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql)
        conn.commit()
        print(f"  OK: {sql[:80]}...")
    except Exception as e:
        print(f"  ERROR: {e}")
    finally:
        conn.close()


def gather_stats():
    """Gather fresh schema statistics for accurate query plans."""
    print("  Gathering schema statistics...")
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("BEGIN DBMS_STATS.GATHER_SCHEMA_STATS(:schema); END;",
                    {"schema": settings.ORACLE_USER.upper()})
        conn.commit()
        print("  OK: Statistics gathered.")
    except Exception as e:
        print(f"  Warning: {e}")
    finally:
        conn.close()


def check_current_partitions():
    """Display current partition status of key tables."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT table_name, COUNT(*) as partition_count
            FROM user_tab_partitions
            GROUP BY table_name
            ORDER BY table_name
        """)
        rows = cur.fetchall()
        if rows:
            for row in rows:
                print(f"  {row[0]}: {row[1]} partitions")
        else:
            print("  No partitions found (heap tables).")
    except Exception as e:
        print(f"  Error checking partitions: {e}")
    finally:
        conn.close()


# -- Scenario setup functions --

def setup_baseline():
    """Remove all partitions by recreating tables as heap (non-partitioned)."""
    print("\n[SETUP] Converting tables to HEAP (no partitions)...")

    steps = [
        # LINEITEM depends on ORDERS, so handle LINEITEM first
        "CREATE TABLE lineitem_temp AS SELECT * FROM lineitem",
        "DROP TABLE lineitem CASCADE CONSTRAINTS",
        "ALTER TABLE lineitem_temp RENAME TO lineitem",

        "CREATE TABLE orders_temp AS SELECT * FROM orders",
        "DROP TABLE orders CASCADE CONSTRAINTS",
        "ALTER TABLE orders_temp RENAME TO orders",
    ]

    for sql in steps:
        execute_ddl(sql)

    gather_stats()
    print("\n[STATUS] Current partition layout:")
    check_current_partitions()


def setup_static_partition():
    """Apply fixed yearly partitioning rules (manual DBA approach)."""
    print("\n[SETUP] Applying STATIC (yearly) partitions...")

    orders_ddl = """
        ALTER TABLE orders MODIFY PARTITION BY RANGE (o_orderdate) (
            PARTITION p_before_1993 VALUES LESS THAN (DATE '1993-01-01'),
            PARTITION p_1993 VALUES LESS THAN (DATE '1994-01-01'),
            PARTITION p_1994 VALUES LESS THAN (DATE '1995-01-01'),
            PARTITION p_1995 VALUES LESS THAN (DATE '1996-01-01'),
            PARTITION p_1996 VALUES LESS THAN (DATE '1997-01-01'),
            PARTITION p_1997 VALUES LESS THAN (DATE '1998-01-01'),
            PARTITION p_1998_onwards VALUES LESS THAN (MAXVALUE)
        ) ONLINE
    """

    lineitem_ddl = """
        ALTER TABLE lineitem MODIFY PARTITION BY RANGE (l_shipdate) (
            PARTITION lp_before_1993 VALUES LESS THAN (DATE '1993-01-01'),
            PARTITION lp_1993 VALUES LESS THAN (DATE '1994-01-01'),
            PARTITION lp_1994 VALUES LESS THAN (DATE '1995-01-01'),
            PARTITION lp_1995 VALUES LESS THAN (DATE '1996-01-01'),
            PARTITION lp_1996 VALUES LESS THAN (DATE '1997-01-01'),
            PARTITION lp_1997 VALUES LESS THAN (DATE '1998-01-01'),
            PARTITION lp_1998_onwards VALUES LESS THAN (MAXVALUE)
        ) ONLINE
    """

    execute_ddl(orders_ddl)
    execute_ddl(lineitem_ddl)
    gather_stats()
    print("\n[STATUS] Current partition layout:")
    check_current_partitions()


def setup_gendba_optimized():
    """Apply Gen-DBA recommended partitions (quarterly granularity based on workload)."""
    print("\n[SETUP] Applying GEN-DBA OPTIMIZED partitions...")

    # First remove existing partitions if static ones are present
    steps = [
        "CREATE TABLE lineitem_temp AS SELECT * FROM lineitem",
        "DROP TABLE lineitem CASCADE CONSTRAINTS",
        "ALTER TABLE lineitem_temp RENAME TO lineitem",

        "CREATE TABLE orders_temp AS SELECT * FROM orders",
        "DROP TABLE orders CASCADE CONSTRAINTS",
        "ALTER TABLE orders_temp RENAME TO orders",
    ]

    for sql in steps:
        execute_ddl(sql)

    # Gen-DBA uses finer-grained partitions based on actual workload analysis
    orders_ddl = """
        ALTER TABLE orders MODIFY PARTITION BY RANGE (o_orderdate) (
            PARTITION p_before_1993 VALUES LESS THAN (DATE '1993-01-01'),
            PARTITION p_1993_h1 VALUES LESS THAN (DATE '1993-07-01'),
            PARTITION p_1993_h2 VALUES LESS THAN (DATE '1994-01-01'),
            PARTITION p_1994_h1 VALUES LESS THAN (DATE '1994-07-01'),
            PARTITION p_1994_h2 VALUES LESS THAN (DATE '1995-01-01'),
            PARTITION p_1995_h1 VALUES LESS THAN (DATE '1995-07-01'),
            PARTITION p_1995_h2 VALUES LESS THAN (DATE '1996-01-01'),
            PARTITION p_1996_h1 VALUES LESS THAN (DATE '1996-07-01'),
            PARTITION p_1996_h2 VALUES LESS THAN (DATE '1997-01-01'),
            PARTITION p_1997_h1 VALUES LESS THAN (DATE '1997-07-01'),
            PARTITION p_1997_h2 VALUES LESS THAN (DATE '1998-01-01'),
            PARTITION p_1998_onwards VALUES LESS THAN (MAXVALUE)
        ) ONLINE
    """

    lineitem_ddl = """
        ALTER TABLE lineitem MODIFY PARTITION BY RANGE (l_shipdate) (
            PARTITION lp_before_1993 VALUES LESS THAN (DATE '1993-01-01'),
            PARTITION lp_1993_h1 VALUES LESS THAN (DATE '1993-07-01'),
            PARTITION lp_1993_h2 VALUES LESS THAN (DATE '1994-01-01'),
            PARTITION lp_1994_h1 VALUES LESS THAN (DATE '1994-07-01'),
            PARTITION lp_1994_h2 VALUES LESS THAN (DATE '1995-01-01'),
            PARTITION lp_1995_h1 VALUES LESS THAN (DATE '1995-07-01'),
            PARTITION lp_1995_h2 VALUES LESS THAN (DATE '1996-01-01'),
            PARTITION lp_1996_h1 VALUES LESS THAN (DATE '1996-07-01'),
            PARTITION lp_1996_h2 VALUES LESS THAN (DATE '1997-01-01'),
            PARTITION lp_1997_h1 VALUES LESS THAN (DATE '1997-07-01'),
            PARTITION lp_1997_h2 VALUES LESS THAN (DATE '1998-01-01'),
            PARTITION lp_1998_onwards VALUES LESS THAN (MAXVALUE)
        ) ONLINE
    """

    execute_ddl(orders_ddl)
    execute_ddl(lineitem_ddl)
    gather_stats()
    print("\n[STATUS] Current partition layout:")
    check_current_partitions()


def run_all_scenarios():
    """Orchestrate all 3 benchmark scenarios and generate comparison report."""
    print("=" * 60)
    print("  GEN-DBA FULL BENCHMARK SUITE")
    print(f"  Started: {datetime.now().isoformat()}")
    print("=" * 60)

    all_results = {}

    # Scenario 1: Baseline (no partitions)
    print("\n\n>>> SCENARIO 1/3: BASELINE (No Partitions)")
    setup_baseline()
    results = run_benchmark("baseline", BENCHMARK_QUERIES)
    baseline_file = save_results("baseline", results)
    all_results["baseline"] = results

    # Scenario 2: Static partitioning (manual yearly)
    print("\n\n>>> SCENARIO 2/3: STATIC PARTITIONING (Yearly)")
    setup_static_partition()
    results = run_benchmark("static_partition", BENCHMARK_QUERIES)
    static_file = save_results("static_partition", results)
    all_results["static"] = results

    # Scenario 3: Gen-DBA optimized (half-yearly granularity)
    print("\n\n>>> SCENARIO 3/3: GEN-DBA OPTIMIZED (Half-Yearly)")
    setup_gendba_optimized()
    results = run_benchmark("gendba_optimized", BENCHMARK_QUERIES)
    gendba_file = save_results("gendba_optimized", results)
    all_results["gendba"] = results

    # Comparison reports
    print("\n\n" + "=" * 80)
    print("  FINAL COMPARISON REPORTS")
    print("=" * 80)

    print("\n--- BASELINE vs STATIC PARTITION ---")
    compare_scenarios(all_results["baseline"], all_results["static"])

    print("\n--- BASELINE vs GEN-DBA OPTIMIZED ---")
    compare_scenarios(all_results["baseline"], all_results["gendba"])

    print("\n--- STATIC PARTITION vs GEN-DBA OPTIMIZED ---")
    compare_scenarios(all_results["static"], all_results["gendba"])

    # Save combined results
    combined_file = f"benchmark_combined_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(combined_file, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "scenarios": all_results,
        }, f, indent=2)
    print(f"\nCombined results saved to: {combined_file}")

    print("\n" + "=" * 60)
    print("  BENCHMARK SUITE COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    run_all_scenarios()
