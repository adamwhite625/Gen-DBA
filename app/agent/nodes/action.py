"""Action node: executes approved DDL scripts with backup and audit."""
import re
from app.agent.state import AgentState, AgentPhase
from app.db.oracle_client import oracle_client
from app.db.ddl_manager import ddl_manager
from app.db.audit import record_audit, AuditEntry
from app.config import settings


def _sanitize_ddl(ddl: str) -> str:
    """Remove physical attributes and trailing semicolons that cause ORA-14020."""
    ddl = ddl.strip().rstrip(';')
    
    # Remove physical attributes Oracle rejects inside PARTITION clauses
    patterns_to_remove = [
        r'\s+TABLESPACE\s+\w+',
        r'\s+PCTFREE\s+\d+',
        r'\s+INITRANS\s+\d+',
        r'\s+MAXTRANS\s+\d+',
        r'\s+LOGGING',
        r'\s+NOLOGGING',
        r'\s+NOCOMPRESS',
        r'\s+COMPRESS\s*\d*',
        r'\s+SEGMENT\s+CREATION\s+\w+',
        r'\s+STORAGE\s*\([^)]*\)',
    ]
    for pattern in patterns_to_remove:
        ddl = re.sub(pattern, '', ddl, flags=re.IGNORECASE)
    
    return ddl.strip()


def _split_ddl_statements(ddl_script: str) -> list[str]:
    """Split multi-statement DDL into individual executable statements."""
    statements = []
    for line in ddl_script.split('\n'):
        line = line.strip().rstrip(';')
        if line and (line.upper().startswith('CREATE ') or 
                     line.upper().startswith('ALTER ') or 
                     line.upper().startswith('DROP ')):
            statements.append(line)
        elif statements:
            # Continuation of previous statement
            statements[-1] += ' ' + line
    
    return [_sanitize_ddl(s) for s in statements if s.strip()]


def action_node(state: AgentState) -> AgentState:
    """Execute the approved DDL scripts safely and audit the operations."""
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
        raw_ddl = rec.ddl_script.strip()
        if not raw_ddl:
            continue

        # Split multi-statement DDL (CTAS + 2 RENAME)
        statements = _split_ddl_statements(raw_ddl)
        
        all_success = True
        executed = []
        error_msg = ""
        
        for stmt in statements:
            result = oracle_client.execute_ddl(stmt)
            if result.get("success"):
                executed.append(stmt)
            else:
                all_success = False
                error_msg = result.get("message", "Unknown error")
                break
        
        # Record audit log
        backup_ddl = ddl_manager.get_table_ddl(rec.target_table) if not all_success else ""
        audit_entry = AuditEntry(
            run_id=state.run_id,
            table_name=rec.target_table,
            operation=rec.strategy,
            ddl_script='\n'.join(executed) if executed else raw_ddl,
            backup_ddl=backup_ddl,
            success=all_success,
            error_message=error_msg
        )
        record_audit(audit_entry)

        if all_success:
            state.executed_ddl.extend(executed)
        else:
            state.error_message += f"Failed on {rec.target_table}: {error_msg} "

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
