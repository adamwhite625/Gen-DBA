"""Benchmark runner that measures query performance across different scenarios."""
import time
import json
import argparse
import oracledb
from datetime import datetime
from statistics import mean, stdev

from app.config import settings
from scripts.benchmark_queries import BENCHMARK_QUERIES

WARMUP_ROUNDS = 2
MEASUREMENT_ROUNDS = 5


class BenchmarkResult:
    """Store results for a single query execution set."""

    def __init__(self, query_name, category):
        self.query_name = query_name
        self.category = category
        self.elapsed_times = []
        self.buffer_gets_list = []
        self.disk_reads_list = []


def flush_caches(cursor):
    """Flush Oracle buffer cache and shared pool for fair measurement."""
    try:
        cursor.execute("ALTER SYSTEM FLUSH BUFFER_CACHE")
        cursor.execute("ALTER SYSTEM FLUSH SHARED_POOL")
    except Exception as e:
        print(f"  Warning: Cannot flush cache: {e}")
        print("  (Requires ALTER SYSTEM privilege)")


def get_sql_stats(cursor, sql_text_prefix):
    """Retrieve execution statistics for the most recently run query."""
    cursor.execute(
        """
        SELECT elapsed_time, buffer_gets, disk_reads, cpu_time
        FROM v$sql
        WHERE sql_text LIKE :prefix
          AND parsing_schema_name = :schema
        ORDER BY last_active_time DESC
        FETCH FIRST 1 ROWS ONLY
        """,
        {"prefix": sql_text_prefix[:50] + "%", "schema": settings.ORACLE_USER.upper()}
    )
    row = cursor.fetchone()
    if row:
        return {
            "elapsed_time_us": row[0],
            "buffer_gets": row[1],
            "disk_reads": row[2],
            "cpu_time_us": row[3],
        }
    return None


def check_partition_pruning(cursor, sql_text):
    """Check whether a query uses partition pruning via EXPLAIN PLAN."""
    try:
        cursor.execute(f"EXPLAIN PLAN FOR {sql_text.strip().rstrip(';')}")
        cursor.execute("SELECT * FROM TABLE(dbms_xplan.display)")
        plan = "\n".join(str(row[0]) for row in cursor.fetchall())
        has_pruning = "PARTITION RANGE" in plan or "Pstart" in plan
        return has_pruning, plan
    except Exception:
        return False, ""


def run_benchmark(scenario_name, queries):
    """Execute all benchmark queries and collect performance metrics."""
    print(f"\n{'='*60}")
    print(f"BENCHMARK: {scenario_name}")
    print(f"{'='*60}")

    conn = oracledb.connect(
        user=settings.ORACLE_USER,
        password=settings.ORACLE_PASSWORD,
        dsn=settings.ORACLE_DSN
    )
    cursor = conn.cursor()

    results = {}

    for qname, qdef in queries.items():
        print(f"\n  Running: {qdef['name']}")
        result = BenchmarkResult(qname, qdef["category"])
        sql = qdef["sql"].strip()

        # Warmup rounds (not measured)
        for _ in range(WARMUP_ROUNDS):
            try:
                cursor.execute(sql)
                cursor.fetchall()
            except Exception:
                pass

        # Measurement rounds
        for i in range(MEASUREMENT_ROUNDS):
            flush_caches(cursor)
            time.sleep(0.5)

            start = time.perf_counter()
            try:
                cursor.execute(sql)
                cursor.fetchall()
            except Exception as e:
                print(f"    Error at round {i+1}: {e}")
                continue
            elapsed = (time.perf_counter() - start) * 1000  # ms

            result.elapsed_times.append(elapsed)

            # Collect Oracle internal stats
            stats = get_sql_stats(cursor, sql[:50])
            if stats:
                result.buffer_gets_list.append(stats["buffer_gets"])
                result.disk_reads_list.append(stats["disk_reads"])

        # Check partition pruning
        has_pruning, plan = check_partition_pruning(cursor, sql)

        # Calculate averages
        if result.elapsed_times:
            avg_time = mean(result.elapsed_times)
            std_time = stdev(result.elapsed_times) if len(result.elapsed_times) > 1 else 0
            print(f"    Avg: {avg_time:.2f}ms (std: {std_time:.2f}ms)")
            print(f"    Partition Pruning: {'YES' if has_pruning else 'NO'}")
        else:
            avg_time = 0
            std_time = 0

        results[qname] = {
            "name": qdef["name"],
            "category": qdef["category"],
            "avg_elapsed_ms": round(avg_time, 2),
            "std_elapsed_ms": round(std_time, 2),
            "min_elapsed_ms": round(min(result.elapsed_times), 2) if result.elapsed_times else 0,
            "max_elapsed_ms": round(max(result.elapsed_times), 2) if result.elapsed_times else 0,
            "avg_buffer_gets": int(mean(result.buffer_gets_list)) if result.buffer_gets_list else 0,
            "avg_disk_reads": int(mean(result.disk_reads_list)) if result.disk_reads_list else 0,
            "partition_pruning": has_pruning,
            "rounds": MEASUREMENT_ROUNDS,
        }

    cursor.close()
    conn.close()

    return results


def save_results(scenario_name, results):
    """Save benchmark results to a JSON file."""
    filename = f"benchmark_{scenario_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump({
            "scenario": scenario_name,
            "timestamp": datetime.now().isoformat(),
            "measurement_rounds": MEASUREMENT_ROUNDS,
            "results": results,
        }, f, indent=2)
    print(f"\nResults saved to: {filename}")
    return filename


def compare_scenarios(baseline_results, optimized_results):
    """Generate a comparison report between two scenarios."""
    print(f"\n{'='*80}")
    print("COMPARISON REPORT")
    print(f"{'='*80}")
    print(f"\n{'Query':<30} {'Baseline(ms)':>13} {'Optimized(ms)':>14} {'Change':>10} {'Pruning':>8}")
    print("-" * 80)

    improvements = []
    for qname in baseline_results:
        if qname in optimized_results:
            base = baseline_results[qname]["avg_elapsed_ms"]
            opt = optimized_results[qname]["avg_elapsed_ms"]
            pruning = "YES" if optimized_results[qname]["partition_pruning"] else "NO"

            if base > 0:
                change_pct = ((opt - base) / base) * 100
                improvements.append(change_pct)
                change_str = f"{change_pct:+.1f}%"
            else:
                change_str = "N/A"

            name = baseline_results[qname]["name"][:28]
            print(f"{name:<30} {base:>13.2f} {opt:>14.2f} {change_str:>10} {pruning:>8}")

    if improvements:
        avg_improvement = mean(improvements)
        print(f"\n{'Average Change:':<30} {'':>13} {'':>14} {avg_improvement:>+9.1f}%")
        print(f"{'Best Improvement:':<30} {'':>13} {'':>14} {min(improvements):>+9.1f}%")
        print(f"{'Worst Change:':<30} {'':>13} {'':>14} {max(improvements):>+9.1f}%")

    return improvements


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Gen-DBA performance benchmark")
    parser.add_argument(
        "--scenario",
        required=True,
        choices=["baseline", "static_partition", "gendba_optimized"],
        help="Benchmark scenario to run"
    )
    args = parser.parse_args()

    results = run_benchmark(args.scenario, BENCHMARK_QUERIES)
    save_results(args.scenario, results)
