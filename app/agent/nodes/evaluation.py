"""Evaluation node: verifies execution results and gathers post-change stats."""
from app.agent.state import AgentState, AgentPhase, PerformanceSnapshot
from app.db.oracle_client import oracle_client
from app.db import queries
from app.config import settings

def evaluation_node(state: AgentState) -> AgentState:
    """Measure performance improvements after DDL execution."""
    state.phase = AgentPhase.EVALUATING

    try:
        schema_name = settings.ORACLE_USER.upper()
        raw_workload = oracle_client.execute_query(
            queries.GET_TOP_SQL,
            {"schema_name": schema_name, "limit": 20}
        )

        if raw_workload:
            total_elapsed = sum(float(w.get("ELAPSED_TIME_MS", 0)) for w in raw_workload)
            total_buffer = sum(int(w.get("BUFFER_GETS", 0)) for w in raw_workload)
            total_disk = sum(int(w.get("DISK_READS", 0)) for w in raw_workload)
            count = len(raw_workload)

            state.after_snapshot = PerformanceSnapshot(
                avg_query_latency_ms=total_elapsed / count,
                total_buffer_gets=total_buffer,
                total_disk_reads=total_disk,
                total_elapsed_time_ms=total_elapsed,
                query_count=count,
            )

        state.improvement_report = _generate_improvement_report(state)
        state.phase = AgentPhase.COMPLETED

    except Exception as e:
        state.phase = AgentPhase.FAILED
        state.error_message = f"Evaluation failed: {str(e)}"

    return state


def _generate_improvement_report(state: AgentState) -> str:
    """Generate a readable comparison of before and after performance."""
    if not state.before_snapshot or not state.after_snapshot:
        return "Insufficient snapshot data for comparison."

    b = state.before_snapshot
    a = state.after_snapshot

    latency_diff = _calculate_percentage_diff(b.avg_query_latency_ms, a.avg_query_latency_ms)
    buffer_diff = _calculate_percentage_diff(b.total_buffer_gets, a.total_buffer_gets)
    disk_diff = _calculate_percentage_diff(b.total_disk_reads, a.total_disk_reads)

    return (
        "Performance Improvement Report\n"
        "------------------------------\n"
        f"Average Query Latency: {b.avg_query_latency_ms:.2f}ms -> {a.avg_query_latency_ms:.2f}ms ({latency_diff})\n"
        f"Total Buffer Gets (I/O): {b.total_buffer_gets} -> {a.total_buffer_gets} ({buffer_diff})\n"
        f"Total Disk Reads: {b.total_disk_reads} -> {a.total_disk_reads} ({disk_diff})\n"
    )

def _calculate_percentage_diff(before: float, after: float) -> str:
    """Calculate and format percentage difference."""
    if before == 0:
        return "N/A"
    change = ((after - before) / before) * 100
    sign = "+" if change > 0 else ""
    return f"{sign}{change:.1f}%"
