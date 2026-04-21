"""Chay cac truy van dang TPC-H de sinh log workload Oracle cho tac tu phan tich."""
import oracledb
import random
import time

# Cau hinh (Sử dụng PDB orclpdb)
DB_USER = "gendba"
DB_PASSWORD = "gendba123"
DB_DSN = "localhost:1521/orclpdb"

QUERIES = [
    # Q1: Quet khoang ngay tren lineitem (Phu hop cho Range Partition)
    """
    SELECT l_returnflag, l_linestatus, SUM(l_quantity) as sum_qty
    FROM lineitem
    WHERE l_shipdate <= DATE '1998-12-01'
    GROUP BY l_returnflag, l_linestatus
    """,
    # Q3: Join Customer, Orders, Lineitem (Phu hop cho Partition-wise join)
    """
    SELECT o_orderkey, o_orderdate, o_shippriority
    FROM customer, orders, lineitem
    WHERE c_mktsegment = 'BUILDING'
      AND c_custkey = o_custkey
      AND l_orderkey = o_orderkey
      AND o_orderdate < DATE '1995-03-15'
      AND l_shipdate > DATE '1995-03-15'
    FETCH FIRST 10 ROWS ONLY
    """,
    # Q6: Loc nhieu dieu kien tren lineitem
    """
    SELECT SUM(l_extendedprice * l_discount) as revenue
    FROM lineitem
    WHERE l_shipdate >= DATE '1994-01-01'
      AND l_shipdate < DATE '1994-01-01' + INTERVAL '1' YEAR
      AND l_discount BETWEEN 0.05 AND 0.07
      AND l_quantity < 24
    """
]

def run_workload(iterations=5):
    """Chay cac truy van nhieu lan de tao workload."""
    try:
        conn = oracledb.connect(user=DB_USER, password=DB_PASSWORD, dsn=DB_DSN)
        cur = conn.cursor()
        
        print(f"Bat dau sinh workload ({iterations} vong)...")
        for i in range(iterations):
            print(f"  Vong {i+1}...")
            for sql in QUERIES:
                cur.execute(sql)
                cur.fetchall()
                time.sleep(0.5) # Nghi giua cac truy van
        
        conn.close()
        print("Sinh workload hoan tat!")
    except Exception as e:
        print(f"Loi: {e}")

if __name__ == "__main__":
    run_workload()
