import time
from app.db.ddl_manager import ddl_manager

def test_ddl_manager():
    print("1. Testing get_table_ddl for table 'ORDERS'...")
    ddl = ddl_manager.get_table_ddl("ORDERS")
    if ddl and not ddl.startswith("Error"):
        print("Successfully retrieved DDL backup.")
        print(f"Preview: {ddl[:200]}...")
    else:
        print(f"Failed to get DDL: {ddl}")

    print("\n2. Testing check_partition_pruning...")
    query = "SELECT * FROM orders WHERE o_orderdate < DATE '1995-01-01'"
    print(f"Query: {query}")
    plan = ddl_manager.check_partition_pruning(query)
    
    print("Execution Plan Raw:", plan)
    for step in plan:
        op = step.get('OPERATION', '')
        opt = step.get('OPTIONS', '')
        obj = step.get('OBJECT_NAME', '')
        p_start = step.get('PARTITION_START', '')
        p_stop = step.get('PARTITION_STOP', '')
        
        # Format the output nicely
        print(f"  - {op} {opt} ON {obj}")
        if p_start or p_stop:
            print(f"    Partition Pruning: Start={p_start}, Stop={p_stop}")

if __name__ == "__main__":
    test_ddl_manager()
