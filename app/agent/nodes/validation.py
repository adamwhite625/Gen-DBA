"""Validation node: validates DDL syntax and safety before execution."""
from app.agent.state import AgentState, AgentPhase

def validation_node(state: AgentState) -> AgentState:
    """Perform automated safety checks on recommended DDLs before human approval."""
    state.phase = AgentPhase.AWAITING_APPROVAL

    # Empty recommendations = all tables already optimized, not an error
    if not state.recommendations:
        return state

    for rec in state.recommendations:
        issues = _safety_check_ddl(rec.ddl_script)
        if issues:
            rec.risk_level = "high"
            rec.reasoning += f"\n\nSAFETY WARNING: {'; '.join(issues)}"

    return state


def _safety_check_ddl(ddl: str) -> list[str]:
    """Check a DDL script for dangerous or unexpected operations."""
    issues = []
    ddl_upper = ddl.upper().strip()

    dangerous_patterns = [
        ("DROP TABLE", "DDL contains DROP TABLE"),
        ("TRUNCATE", "DDL contains TRUNCATE"),
        ("DROP PARTITION", "DDL contains DROP PARTITION"),
        ("CASCADE", "DDL contains CASCADE"),
    ]
    for pattern, warning in dangerous_patterns:
        if pattern in ddl_upper:
            issues.append(warning)

    # Accept both ALTER TABLE and CREATE TABLE (CTAS approach)
    valid_starts = ("ALTER TABLE", "CREATE TABLE")
    if not any(ddl_upper.startswith(s) for s in valid_starts):
        issues.append("DDL does not start with ALTER TABLE or CREATE TABLE")

    if ';' in ddl and ddl.strip()[-1] == ';':
        issues.append("DDL contains trailing semicolon (not recommended for execution)")

    return issues


def apply_approval(state: AgentState, approved: bool, notes: str = "") -> AgentState:
    """Update state based on human DBA decision."""
    state.is_approved = approved
    if approved:
        state.phase = AgentPhase.EXECUTING
    else:
        state.phase = AgentPhase.COMPLETED
        state.error_message = f"Rejected by DBA: {notes}"

    return state
