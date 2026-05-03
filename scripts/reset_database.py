"""Reset database to original TPC-H state (before any fragmentation)."""
import sys
sys.path.insert(0, '.')

from app.db.oracle_client import oracle_client

# Order matters: aggressively drop everything we created, then restore from backups
RESET_STEPS = [
    # Drop views if they exist
    ("DROP VIEW ORDERS", "Drop ORDERS view"),
    ("DROP VIEW LINEITEM", "Drop LINEITEM view"),
    
    # Drop tables if they exist (in case they were not views but partitioned tables)
    ("DROP TABLE ORDERS PURGE", "Drop ORDERS table (if partitioned)"),
    ("DROP TABLE LINEITEM PURGE", "Drop LINEITEM table (if partitioned)"),
    
    # Drop any leftover fragmented or partitioned tables
    ("DROP TABLE ORDERS_MAIN PURGE", "Drop ORDERS_MAIN"),
    ("DROP TABLE ORDERS_DETAIL PURGE", "Drop ORDERS_DETAIL"),
    ("DROP TABLE LINEITEM_MAIN PURGE", "Drop LINEITEM_MAIN"),
    ("DROP TABLE LINEITEM_DETAIL PURGE", "Drop LINEITEM_DETAIL"),
    ("DROP TABLE ORDERS_PARTITIONED PURGE", "Drop ORDERS_PARTITIONED"),
    ("DROP TABLE LINEITEM_PARTITIONED PURGE", "Drop LINEITEM_PARTITIONED"),
    
    # Finally, rename backup tables back to original names
    ("ALTER TABLE ORDERS_HEAP_BACKUP RENAME TO ORDERS", "Restore ORDERS from backup"),
    ("ALTER TABLE LINEITEM_HEAP_BACKUP RENAME TO LINEITEM", "Restore LINEITEM from backup"),
]


def reset_database():
    """Restore original heap tables from backups and remove all fragmentation artifacts."""
    print("=== RESET DATABASE TO ORIGINAL TPC-H STATE ===\n")
    
    # 1. Clean up views and fragmented tables
    cleanups = [
        ("DROP VIEW ORDERS", "Drop ORDERS view"),
        ("DROP VIEW LINEITEM", "Drop LINEITEM view"),
        ("DROP TABLE ORDERS_MAIN PURGE", "Drop ORDERS_MAIN"),
        ("DROP TABLE ORDERS_DETAIL PURGE", "Drop ORDERS_DETAIL"),
        ("DROP TABLE LINEITEM_MAIN PURGE", "Drop LINEITEM_MAIN"),
        ("DROP TABLE LINEITEM_DETAIL PURGE", "Drop LINEITEM_DETAIL"),
        ("DROP TABLE ORDERS_PARTITIONED PURGE", "Drop ORDERS_PARTITIONED"),
        ("DROP TABLE LINEITEM_PARTITIONED PURGE", "Drop LINEITEM_PARTITIONED"),
    ]
    
    for ddl, desc in cleanups:
        print(f"  [{desc}] ... ", end="")
        result = oracle_client.execute_ddl(ddl)
        msg = result.get("message", "")
        if result.get("success"):
            print("OK")
        elif "ORA-00942" in msg or "ORA-04043" in msg or "ORA-12003" in msg:
            print("SKIPPED (not found)")
        else:
            print(f"ERROR: {msg}")

    # 2. Check and restore ORDERS
    print("  [Restore ORDERS from backup] ... ", end="")
    check_orders = oracle_client.execute_query("SELECT table_name FROM user_tables WHERE table_name = 'ORDERS_HEAP_BACKUP'")
    if check_orders:
        oracle_client.execute_ddl("DROP TABLE ORDERS PURGE")
        res = oracle_client.execute_ddl("ALTER TABLE ORDERS_HEAP_BACKUP RENAME TO ORDERS")
        print("OK" if res.get("success") else f"ERROR: {res.get('message')}")
    else:
        print("SKIPPED (No backup found, assuming ORDERS is already original)")

    # 3. Check and restore LINEITEM
    print("  [Restore LINEITEM from backup] ... ", end="")
    check_lineitem = oracle_client.execute_query("SELECT table_name FROM user_tables WHERE table_name = 'LINEITEM_HEAP_BACKUP'")
    if check_lineitem:
        oracle_client.execute_ddl("DROP TABLE LINEITEM PURGE")
        res = oracle_client.execute_ddl("ALTER TABLE LINEITEM_HEAP_BACKUP RENAME TO LINEITEM")
        print("OK" if res.get("success") else f"ERROR: {res.get('message')}")
    else:
        print("SKIPPED (No backup found, assuming LINEITEM is already original)")
    
    # Gather fresh statistics
    print("\n  [Gather schema stats] ... ", end="")
    try:
        oracle_client.execute_ddl(
            "BEGIN DBMS_STATS.GATHER_SCHEMA_STATS('GENDBA'); END;"
        )
        print("OK")
    except Exception:
        print("SKIPPED")
    
    # Verify final state
    print("\n=== VERIFICATION ===")
    rows = oracle_client.execute_query("""
        SELECT object_name, object_type 
        FROM user_objects 
        WHERE object_type IN ('TABLE', 'VIEW')
          AND object_name NOT LIKE 'BIN$%'
          AND object_name NOT LIKE 'PLAN_%'
          AND object_name != 'GENDBA_AUDIT'
        ORDER BY object_type, object_name
    """)
    
    for r in rows:
        print(f"  {r['OBJECT_TYPE']:6s} {r['OBJECT_NAME']}")
    
    print("\nDatabase reset complete. You can now run Agent Analysis from scratch.")


if __name__ == "__main__":
    reset_database()
