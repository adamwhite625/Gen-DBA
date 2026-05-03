import oracledb
import time
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
from app.config import settings
from scripts.benchmark import run_benchmark, save_results
from scripts.benchmark_queries import BENCHMARK_QUERIES

def apply_mixed_fragmentation():
    print("\n--- BƯỚC 6.5: THỰC HIỆN PHÂN MẢNH HỖN HỢP (Ngang + Dọc) ---")
    conn = oracledb.connect(
        user=settings.ORACLE_USER,
        password=settings.ORACLE_PASSWORD,
        dsn=settings.ORACLE_DSN
    )
    cur = conn.cursor()

    orders_ddl = """
        CREATE TABLE orders_main_part 
        PARTITION BY RANGE (o_orderdate) (
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
        )
        AS SELECT * FROM orders_main
    """
    print("Partitioning orders_main...")
    try: 
        cur.execute("DROP TABLE orders_main_part CASCADE CONSTRAINTS")
    except: pass
    try: 
        cur.execute(orders_ddl)
        cur.execute("DROP TABLE orders_main CASCADE CONSTRAINTS")
        cur.execute("RENAME orders_main_part TO orders_main")
        cur.execute("ALTER TABLE orders_main ADD CONSTRAINT orders_main_pk PRIMARY KEY (o_orderkey)")
    except Exception as e: print(f"Warning: {e}")

    lineitem_ddl = """
        CREATE TABLE lineitem_main_part 
        PARTITION BY RANGE (l_shipdate) (
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
        )
        AS SELECT * FROM lineitem_main
    """
    print("Partitioning lineitem_main...")
    try: 
        cur.execute("DROP TABLE lineitem_main_part CASCADE CONSTRAINTS")
    except: pass
    try: 
        cur.execute(lineitem_ddl)
        cur.execute("DROP TABLE lineitem_main CASCADE CONSTRAINTS")
        cur.execute("RENAME lineitem_main_part TO lineitem_main")
        cur.execute("ALTER TABLE lineitem_main ADD CONSTRAINT lineitem_main_pk PRIMARY KEY (l_orderkey, l_linenumber)")
    except Exception as e: print(f"Warning: {e}")

    # For True Transparency, we rename original tables and replace them with the views!
    print("Setting up true transparency for benchmarks (renaming views to original table names)...")
    transparency_commands = [
        "RENAME orders TO orders_heap_backup",
        "RENAME lineitem TO lineitem_heap_backup",
        "CREATE OR REPLACE VIEW orders AS SELECT m.o_orderkey, m.o_custkey, m.o_orderstatus, m.o_totalprice, m.o_orderdate, d.o_orderpriority, d.o_clerk, d.o_shippriority, d.o_comment FROM orders_main m JOIN orders_detail@site2_link d ON m.o_orderkey = d.o_orderkey",
        "CREATE OR REPLACE VIEW lineitem AS SELECT m.l_orderkey, m.l_partkey, m.l_suppkey, m.l_linenumber, m.l_quantity, m.l_extendedprice, d.l_discount, d.l_tax, d.l_returnflag, d.l_linestatus, m.l_shipdate, d.l_commitdate, d.l_receiptdate, d.l_shipinstruct, d.l_shipmode, d.l_comment FROM lineitem_main m JOIN lineitem_detail@site2_link d ON m.l_orderkey = d.l_orderkey AND m.l_linenumber = d.l_linenumber"
    ]
    for cmd in transparency_commands:
        try:
            cur.execute(cmd)
        except Exception as e:
            if "ORA-00955" not in str(e): # Name already used
                print(f"Transparency setup: {e}")

    # Gather stats to help optimizer
    print("Gathering statistics...")
    cur.execute("BEGIN DBMS_STATS.GATHER_SCHEMA_STATS('GENDBA'); END;")

    conn.commit()
    cur.close()
    conn.close()
    print("Bước 6.5 hoàn tất! (Hỗn hợp: Vertical Main + Horizontal Range)")

def run_mixed_benchmark():
    print("\n--- BƯỚC 6.6: BENCHMARK KỊCH BẢN PHÂN TÁN HỖN HỢP ---")
    
    # We will run the same BENCHMARK_QUERIES
    # Because we renamed the views to "orders" and "lineitem", the queries will naturally
    # hit the distributed views!
    results = run_benchmark("full_distributed", BENCHMARK_QUERIES)
    
    # Save results to json
    save_results("full_distributed", results)
    
    # Let's compare this with the latest baseline we have, or just print the metrics.
    # To show it clearly, we will print out the final stats
    print("\n--- KẾT QUẢ BENCHMARK FULL DISTRIBUTED (HỖN HỢP) ---")
    for qname, q in results.items():
        print(f"\nQuery: {q['name']}")
        print(f"  Avg Elapsed Time: {q['avg_elapsed_ms']:.2f} ms")
        print(f"  Buffer Gets: {q['avg_buffer_gets']}")
        print(f"  Disk Reads: {q['avg_disk_reads']}")
        print(f"  Pruning: {q['partition_pruning']}")

if __name__ == "__main__":
    apply_mixed_fragmentation()
    run_mixed_benchmark()
