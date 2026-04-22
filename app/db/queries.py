"""Predefined Oracle SQL queries for gathering workload and metadata."""

GET_TOP_SQL = """
    SELECT sql_id, sql_text, executions,
           ROUND(elapsed_time / 1000, 2) as elapsed_time_ms,
           buffer_gets, disk_reads
    FROM v$sqlarea
    WHERE parsing_schema_name = :schema_name
      AND executions > 0
      AND sql_text NOT LIKE '%v$%'
      AND sql_text NOT LIKE '%DBA_%'
    ORDER BY elapsed_time DESC
    FETCH FIRST :limit ROWS ONLY
"""

GET_TABLE_STATS = """
    SELECT table_name, num_rows, avg_row_len, last_analyzed
    FROM dba_tables
    WHERE owner = :schema_name
      AND table_name IN ('ORDERS', 'LINEITEM', 'CUSTOMER', 'SUPPLIER', 'PART')
"""
