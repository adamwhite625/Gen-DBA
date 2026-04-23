"""Unit tests for Oracle database connection and queries."""
from app.db.oracle_client import oracle_client
from app.config import settings

def test_connection():
    """Verify that the Oracle connection is active and returns version."""
    result = oracle_client.test_connection()
    assert result["connected"] is True, f"Connection failed: {result.get('error')}"
    assert "19" in result["version"], "Expected Oracle version 19"

def test_query_vsql():
    """Verify that V$SQLAREA is accessible."""
    rows = oracle_client.execute_query(
        "SELECT COUNT(*) as cnt FROM v$sqlarea WHERE ROWNUM <= 1"
    )
    assert len(rows) == 1
    assert rows[0]["CNT"] >= 0

def test_query_tables():
    """Verify that TPC-H tables exist in the schema."""
    schema_name = settings.ORACLE_USER.upper()
    rows = oracle_client.execute_query(
        f"""
        SELECT table_name FROM dba_tables
        WHERE owner = '{schema_name}' AND table_name = 'ORDERS'
        """
    )
    assert len(rows) == 1, f"Table 'ORDERS' not found in schema {schema_name}"

if __name__ == "__main__":
    test_connection()
    print("PASS: test_connection")
    test_query_vsql()
    print("PASS: test_query_vsql")
    test_query_tables()
    print("PASS: test_query_tables")
    print("\nAll tests passed successfully!")
