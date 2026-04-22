from app.agent.state import AgentState, AgentPhase
from app.db.oracle_client import oracle_client
from app.config import settings

def action_node(state: AgentState) -> AgentState:
    """Execute the approved DDL scripts on the Oracle database."""
    state.phase = AgentPhase.EXECUTING

    if not state.is_approved:
        state.phase = AgentPhase.COMPLETED
        state.error_message = "Execution skipped: not approved by DBA."
        return state

    if not state.recommendations:
        state.phase = AgentPhase.FAILED
        state.error_message = "No DDL scripts available for execution."
        return state

    for rec in state.recommendations:
        ddl = rec.ddl_script.strip().rstrip(';')

        if not ddl:
            continue

        result = oracle_client.execute_ddl(ddl)
        
        if result.get("success"):
            state.executed_ddl.append(ddl)
        else:
            state.error_message += f"Failed on {rec.target_table}: {result.get('message')}\n"

    _gather_schema_stats()

    if state.executed_ddl:
        state.phase = AgentPhase.EVALUATING
    else:
        state.phase = AgentPhase.FAILED
        if not state.error_message:
            state.error_message = "All DDL executions failed."

    return state


def _gather_schema_stats():
    """Gather Oracle schema statistics after partitioning changes."""
    schema_name = settings.ORACLE_USER.upper()
    try:
        oracle_client.execute_ddl(
            f"BEGIN DBMS_STATS.GATHER_SCHEMA_STATS('{schema_name}'); END;"
        )
    except Exception:
        pass
