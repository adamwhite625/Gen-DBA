"""Perception node: collects workload data and schema context from Oracle."""
from app.agent.state import AgentState, AgentPhase, WorkloadEntry, PerformanceSnapshot
from app.db.oracle_client import oracle_client
from app.db import queries
from app.config import settings


# Query to discover actual tables vs views in the schema
GET_SCHEMA_OBJECTS = """
    SELECT object_name, object_type 
    FROM all_objects 
    WHERE owner = :schema_name 
      AND object_type IN ('TABLE', 'VIEW')
      AND object_name NOT LIKE 'BIN$%'
      AND object_name NOT LIKE 'PLAN_%'
    ORDER BY object_type, object_name
"""


def _build_schema_context(schema_name: str) -> str:
    """Query Oracle to build a description of actual tables, views, and partition status."""
    try:
        rows = oracle_client.execute_query(
            GET_SCHEMA_OBJECTS,
            {"schema_name": schema_name}
        )
        
        tables = [r["OBJECT_NAME"] for r in rows if r["OBJECT_TYPE"] == "TABLE"]
        views = [r["OBJECT_NAME"] for r in rows if r["OBJECT_TYPE"] == "VIEW"]
        
        # Check which tables are already partitioned
        part_rows = oracle_client.execute_query("""
            SELECT table_name, partitioning_type, partitioning_key_columns 
            FROM (
                SELECT pt.table_name, pt.partitioning_type,
                       LISTAGG(kc.column_name, ', ') WITHIN GROUP (ORDER BY kc.column_position) as partitioning_key_columns
                FROM user_part_tables pt
                JOIN user_part_key_columns kc ON pt.table_name = kc.name
                GROUP BY pt.table_name, pt.partitioning_type
            )
        """)
        
        already_partitioned = {r["TABLE_NAME"]: f"{r['PARTITIONING_TYPE']} on {r['PARTITIONING_KEY_COLUMNS']}" for r in part_rows}
        
        lines = ["Current Schema Objects:"]
        lines.append(f"TABLES: {', '.join(tables) if tables else 'None'}")
        lines.append(f"VIEWS: {', '.join(views) if views else 'None'}")
        
        if already_partitioned:
            lines.append("")
            lines.append("ALREADY PARTITIONED TABLES (DO NOT re-partition these):")
            for tname, pinfo in already_partitioned.items():
                lines.append(f"  - {tname}: {pinfo}")
        
        # Find candidate tables that are NOT partitioned and NOT backups
        # Only include tables with significant row count (>10000)
        row_counts = {}
        try:
            size_rows = oracle_client.execute_query("""
                SELECT table_name, NVL(num_rows, 0) as num_rows 
                FROM user_tables 
                WHERE table_name NOT LIKE 'BIN$%'
            """)
            row_counts = {r["TABLE_NAME"]: r["NUM_ROWS"] for r in size_rows}
        except Exception:
            pass
        
        unpartitioned = [t for t in tables 
                         if t not in already_partitioned 
                         and not t.endswith('_BACKUP')
                         and t not in ('GENDBA_AUDIT',)
                         and row_counts.get(t, 0) > 10000]
        
        if unpartitioned:
            lines.append(f"\nUnpartitioned candidate tables (>10000 rows):")
            for t in unpartitioned:
                lines.append(f"  - {t} ({row_counts.get(t, 'unknown')} rows)")
                # Show actual columns so LLM doesn't hallucinate
                try:
                    cols = oracle_client.execute_query(f"""
                        SELECT column_name, data_type 
                        FROM user_tab_columns 
                        WHERE table_name = '{t}' 
                        ORDER BY column_id
                    """)
                    col_list = [f"{c['COLUMN_NAME']}({c['DATA_TYPE']})" for c in cols]
                    lines.append(f"    Columns: {', '.join(col_list)}")
                except Exception:
                    pass
        else:
            lines.append("\nAll large tables are already partitioned. No action needed.")
            lines.append("Return an empty JSON array: []")
        
        if views:
            lines.append(f"\nWARNING: These are VIEWs, NOT tables: {', '.join(views)}")
            lines.append("Do NOT target VIEWs for partitioning.")
        
        return "\n".join(lines)
    except Exception as e:
        return f"Error fetching schema: {str(e)}"


def perception_node(state: AgentState) -> AgentState:
    """Fetch top resource-consuming SQL queries and schema context from Oracle."""
    state.phase = AgentPhase.PERCEIVING
    schema_name = settings.ORACLE_USER.upper()

    try:
        raw_workload = oracle_client.execute_query(
            queries.GET_TOP_SQL,
            {"schema_name": schema_name, "limit": 20}
        )
        
        state.workload_entries = [
            WorkloadEntry(
                sql_id=row["SQL_ID"],
                sql_text=row["SQL_TEXT"],
                executions=row["EXECUTIONS"],
                elapsed_time_ms=row["ELAPSED_TIME_MS"],
                buffer_gets=row["BUFFER_GETS"],
                disk_reads=row["DISK_READS"]
            ) for row in raw_workload
        ]

        # Build schema context so LLM knows which objects are tables vs views
        state.schema_context = _build_schema_context(schema_name)

        if not state.before_snapshot and state.workload_entries:
            total_elapsed = sum(w.elapsed_time_ms for w in state.workload_entries)
            total_buffer = sum(w.buffer_gets for w in state.workload_entries)
            total_disk = sum(w.disk_reads for w in state.workload_entries)
            count = len(state.workload_entries)

            state.before_snapshot = PerformanceSnapshot(
                avg_query_latency_ms=total_elapsed / count,
                total_buffer_gets=total_buffer,
                total_disk_reads=total_disk,
                total_elapsed_time_ms=total_elapsed,
                query_count=count,
            )
            
    except Exception as e:
        state.phase = AgentPhase.FAILED
        state.error_message = f"Perception failed: {str(e)}"

        
    return state
