from app.agent.state import AgentState, AgentPhase, WorkloadEntry, PerformanceSnapshot
from app.db.oracle_client import oracle_client
from app.db import queries
from app.config import settings

def perception_node(state: AgentState) -> AgentState:
    """Fetch top resource-consuming SQL queries from V$SQL in the database."""
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
