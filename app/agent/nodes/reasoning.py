import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from app.agent.state import AgentState, AgentPhase, PartitionRecommendation
from app.agent.prompts.analyze_workload import SYSTEM_PROMPT, ANALYSIS_PROMPT_TEMPLATE
from app.config import settings


def _build_workload_summary(state: AgentState) -> str:
    """Format the workload data into a readable string for the LLM prompt."""
    if not state.workload_entries:
        return "No workload data available."
    
    lines = ["Oracle Workload Analysis Report\n"]
    lines.append("Top SQL by Elapsed Time")
    lines.append(f"{'SQL_ID':<15} {'Execs':>6} {'Time(ms)':>12} {'BufGets':>10} {'DiskRd':>8}")
    
    for w in state.workload_entries[:15]:
        lines.append(
            f"{w.sql_id:<15} {w.executions:>6} {w.elapsed_time_ms:>12.1f} "
            f"{w.buffer_gets:>10} {w.disk_reads:>8}"
        )
        sql_preview = w.sql_text.replace('\n', ' ')[:120]
        lines.append(f"SQL: {sql_preview}")
        
    return "\n".join(lines)


def reasoning_node(state: AgentState) -> AgentState:
    """Invoke the LLM to analyze the workload and generate partitioning recommendations."""
    state.phase = AgentPhase.REASONING

    if not state.workload_entries:
        state.phase = AgentPhase.FAILED
        state.error_message = "No workload data available for reasoning."
        return state

    try:
        workload_summary = _build_workload_summary(state)
        
        llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            api_key=settings.OPENAI_API_KEY,
            temperature=0.1
        )

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=ANALYSIS_PROMPT_TEMPLATE.format(
                workload_summary=workload_summary
            ))
        ]

        response = llm.invoke(messages)
        recommendations = _parse_llm_response(response.content)
        state.recommendations = recommendations

        if not recommendations:
            state.phase = AgentPhase.FAILED
            state.error_message = "LLM returned invalid or empty recommendations."
            return state

        state.phase = AgentPhase.AWAITING_APPROVAL

    except Exception as e:
        state.phase = AgentPhase.FAILED
        state.error_message = f"Reasoning failed: {str(e)}"

    return state


def _parse_llm_response(raw_response: str) -> list[PartitionRecommendation]:
    """Extract and parse structured JSON recommendations from the LLM response."""
    cleaned = raw_response.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned.split("\n", 1)[1]
    if cleaned.endswith("```"):
        cleaned = cleaned.rsplit("```", 1)[0]
    cleaned = cleaned.strip()

    try:
        data = json.loads(cleaned)
        if isinstance(data, dict):
            data = [data]

        recommendations = []
        for item in data:
            rec = PartitionRecommendation(
                target_table=item.get("target_table", ""),
                strategy=item.get("strategy", "RANGE"),
                partition_key=item.get("partition_key", ""),
                ddl_script=item.get("ddl_script", ""),
                reasoning=item.get("reasoning", ""),
                risk_level=item.get("risk_level", "medium"),
            )
            recommendations.append(rec)

        return recommendations

    except json.JSONDecodeError:
        return []
