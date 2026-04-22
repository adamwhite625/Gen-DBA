from fastapi import APIRouter, HTTPException
from app.agent.graph import agent_graph, create_new_run
from app.api.routes.partitions import pending_states

router = APIRouter()

@router.post("/analyze")
async def start_analysis():
    """Trigger the perception and reasoning pipeline to generate partitioning recommendations."""
    initial_state = create_new_run()
    
    try:
        # Run graph from perception -> reasoning -> validation
        result_state = agent_graph.invoke(initial_state.model_dump())
        run_id = initial_state.run_id
        
        # Save state in memory for approval step
        from app.agent.state import AgentState
        final_state = AgentState(**result_state)
        pending_states[run_id] = final_state

        return {
            "run_id": run_id,
            "phase": final_state.phase.value,
            "recommendations": [r.model_dump() for r in final_state.recommendations],
            "error": final_state.error_message
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/execute/{run_id}")
async def execute_approved_recommendation(run_id: str):
    """Execute the DDL scripts after human approval."""
    if run_id not in pending_states:
        raise HTTPException(status_code=404, detail="Run ID not found or already executed.")

    state = pending_states[run_id]

    if state.phase.value != "executing":
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot execute. Current phase is {state.phase.value}. Ensure it is approved."
        )

    try:
        # Start graph explicitly from the action node
        # Wait, LangGraph invoke with entry point is slightly different.
        # But for simplicity, we can just call the nodes sequentially here, 
        # or use standard Langgraph thread checkpointing. 
        # Since we use simple StateGraph without checkpointing DB:
        from app.agent.nodes.action import action_node
        from app.agent.nodes.evaluation import evaluation_node

        # Manual trigger of remaining nodes
        state = action_node(state)
        if state.phase.value == "evaluating":
            state = evaluation_node(state)

        pending_states[run_id] = state

        return {
            "run_id": run_id,
            "phase": state.phase.value,
            "executed_ddl": state.executed_ddl,
            "improvement_report": state.improvement_report,
            "error": state.error_message
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{run_id}")
async def get_agent_status(run_id: str):
    """Check the current status of an agent run."""
    if run_id not in pending_states:
        raise HTTPException(status_code=404, detail="Run ID not found.")
    
    state = pending_states[run_id]
    return {
        "run_id": run_id,
        "phase": state.phase.value,
        "error": state.error_message
    }
