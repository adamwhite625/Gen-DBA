"""Benchmark query definitions based on TPC-H workload for partition evaluation."""

BENCHMARK_QUERIES = {
    "Q1_pricing_summary": {
        "name": "Pricing Summary (date filter on lineitem)",
        "sql": """
            SELECT l_returnflag, l_linestatus,
                   SUM(l_quantity), SUM(l_extendedprice),
                   SUM(l_extendedprice * (1 - l_discount)),
                   AVG(l_quantity), AVG(l_extendedprice), COUNT(*)
            FROM lineitem
            WHERE l_shipdate <= DATE '1998-09-02'
            GROUP BY l_returnflag, l_linestatus
            ORDER BY l_returnflag, l_linestatus
        """,
        "category": "date_range_scan",
    },
    "Q3_shipping_priority": {
        "name": "Shipping Priority (join with date filter)",
        "sql": """
            SELECT o_orderkey,
                   SUM(l_extendedprice * (1 - l_discount)) as revenue,
                   o_orderdate, o_shippriority
            FROM customer, orders, lineitem
            WHERE c_mktsegment = 'BUILDING'
              AND c_custkey = o_custkey
              AND l_orderkey = o_orderkey
              AND o_orderdate < DATE '1995-03-15'
              AND l_shipdate > DATE '1995-03-15'
            GROUP BY o_orderkey, o_orderdate, o_shippriority
            ORDER BY revenue DESC, o_orderdate
            FETCH FIRST 10 ROWS ONLY
        """,
        "category": "join_with_date_filter",
    },
    "Q4_order_priority": {
        "name": "Order Priority Check (date range on orders)",
        "sql": """
            SELECT o_orderpriority, COUNT(*) as order_count
            FROM orders
            WHERE o_orderdate >= DATE '1993-07-01'
              AND o_orderdate < DATE '1993-10-01'
            GROUP BY o_orderpriority
            ORDER BY o_orderpriority
        """,
        "category": "date_range_scan",
    },
    "Q6_revenue_forecast": {
        "name": "Revenue Change Forecast (date + filter on lineitem)",
        "sql": """
            SELECT SUM(l_extendedprice * l_discount) as revenue
            FROM lineitem
            WHERE l_shipdate >= DATE '1994-01-01'
              AND l_shipdate < DATE '1995-01-01'
              AND l_discount BETWEEN 0.05 AND 0.07
              AND l_quantity < 24
        """,
        "category": "date_range_scan",
    },
    "Q5_local_supplier_volume": {
        "name": "Local Supplier Volume (multi-join with date)",
        "sql": """
            SELECT n_name, SUM(l_extendedprice * (1 - l_discount)) as revenue
            FROM customer, orders, lineitem, supplier, nation, region
            WHERE c_custkey = o_custkey
              AND l_orderkey = o_orderkey
              AND l_suppkey = s_suppkey
              AND c_nationkey = s_nationkey
              AND s_nationkey = n_nationkey
              AND n_regionkey = r_regionkey
              AND r_name = 'ASIA'
              AND o_orderdate >= DATE '1994-01-01'
              AND o_orderdate < DATE '1995-01-01'
            GROUP BY n_name
            ORDER BY revenue DESC
        """,
        "category": "multi_join_date_filter",
    },
    "Q12_shipping_mode": {
        "name": "Shipping Mode (date range on lineitem)",
        "sql": """
            SELECT l_shipmode,
                   SUM(CASE WHEN o_orderpriority = '1-URGENT'
                             OR o_orderpriority = '2-HIGH' THEN 1 ELSE 0 END) as high_line_count,
                   SUM(CASE WHEN o_orderpriority != '1-URGENT'
                            AND o_orderpriority != '2-HIGH' THEN 1 ELSE 0 END) as low_line_count
            FROM orders, lineitem
            WHERE o_orderkey = l_orderkey
              AND l_shipmode IN ('MAIL', 'SHIP')
              AND l_commitdate < l_receiptdate
              AND l_shipdate < l_commitdate
              AND l_receiptdate >= DATE '1994-01-01'
              AND l_receiptdate < DATE '1995-01-01'
            GROUP BY l_shipmode
            ORDER BY l_shipmode
        """,
        "category": "date_range_join",
    },
    "Q14_promotion_effect": {
        "name": "Promotion Effect (date range on lineitem)",
        "sql": """
            SELECT 100.00 * SUM(CASE WHEN p_type LIKE 'PROMO%%'
                                     THEN l_extendedprice * (1 - l_discount)
                                     ELSE 0 END)
                   / SUM(l_extendedprice * (1 - l_discount)) as promo_revenue
            FROM lineitem, part
            WHERE l_partkey = p_partkey
              AND l_shipdate >= DATE '1995-09-01'
              AND l_shipdate < DATE '1995-10-01'
        """,
        "category": "date_range_join",
    },
    "full_table_scan": {
        "name": "Full Table Scan (no filter - worst case)",
        "sql": "SELECT COUNT(*), AVG(o_totalprice) FROM orders",
        "category": "full_scan",
    },
}
