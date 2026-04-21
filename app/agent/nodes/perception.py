"""Node Thu Thap: Thu thap thong tin workload tu Oracle."""
from app.agent.state import AgentState, AgentPhase, WorkloadEntry
from app.db.oracle_client import oracle_client
from app.db import queries
from app.config import settings

def perception_node(state: AgentState) -> AgentState:
    """
    Truy van V$SQL de lay danh sach cac cau lenh SQL dang tieu ton tai nguyen.
    """
    print("--- NODE: PERCEPTION ---")
    state.phase = AgentPhase.PERCEIVING
    schema_name = settings.ORACLE_USER.upper()

    try:
        # Lay top SQL
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
        
        print(f"  Thu thap duoc {len(state.workload_entries)} cau lenh SQL.")
        
    except Exception as e:
        state.phase = AgentPhase.FAILED
        state.error_message = f"Perception failed: {str(e)}"
        print(f"  Loi: {e}")
        
    return state
