"""API routes for performance metrics, benchmarking, and audit trail."""
from fastapi import APIRouter
from app.db.oracle_client import oracle_client
from app.db.audit import get_audit_history
from app.config import settings

router = APIRouter()

@router.get("/performance")
async def get_performance_metrics():
    """Return overview of current database performance."""
    schema = settings.ORACLE_USER.upper()

    # Top resource-consuming queries
    top_queries = oracle_client.execute_query(
        """
        SELECT sql_id,
               SUBSTR(sql_text, 1, 100) as sql_preview,
               executions,
               ROUND(elapsed_time/1000, 2) as elapsed_ms,
               buffer_gets,
               disk_reads
        FROM v$sqlarea
        WHERE parsing_schema_name = :schema
          AND executions > 0
        ORDER BY elapsed_time DESC
        FETCH FIRST 10 ROWS ONLY
        """,
        {"schema": schema}
    )

    # Table sizes
    table_sizes = oracle_client.execute_query(
        """
        SELECT table_name, num_rows,
               ROUND(num_rows * avg_row_len / 1024 / 1024, 2) as est_size_mb
        FROM dba_tables
        WHERE owner = :schema
          AND num_rows > 0
        ORDER BY num_rows DESC
        """,
        {"schema": schema}
    )

    return {
        "top_queries": top_queries,
        "table_sizes": table_sizes,
    }

@router.get("/partitions/summary")
async def get_partition_summary():
    """Return a summary of partitioned tables."""
    schema = settings.ORACLE_USER.upper()

    partitions = oracle_client.execute_query(
        """
        SELECT table_name,
               COUNT(*) as partition_count,
               SUM(num_rows) as total_rows
        FROM dba_tab_partitions
        WHERE table_owner = :schema
        GROUP BY table_name
        ORDER BY table_name
        """,
        {"schema": schema}
    )

    return {"partitioned_tables": partitions}

@router.get("/audit")
async def get_audit_trail():
    """Return the audit log of executed DDLs."""
    return {"audit_entries": get_audit_history()}

@router.get("/health/oracle")
async def check_oracle_health():
    """Check connection and status of Oracle Database."""
    result = oracle_client.test_connection()
    return result
