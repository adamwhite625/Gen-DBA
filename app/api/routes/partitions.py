from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

router = APIRouter()

# In-memory store for pending approvals (replace with Redis/DB in production)
pending_states: Dict[str, Any] = {}

class ApprovalRequest(BaseModel):
    approved: bool
    notes: str = ""

@router.get("/current")
async def get_current_partitions():
    """Retrieve existing partitions from the Oracle database."""
    from app.db.oracle_client import oracle_client
    from app.db import queries
    from app.config import settings

    try:
        partitions = oracle_client.execute_query(
            "SELECT table_name, partition_name, high_value FROM dba_tab_partitions WHERE table_owner = :schema_name",
            {"schema_name": settings.ORACLE_USER.upper()}
        )
        return {"partitions": partitions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/pending")
async def get_pending_approvals():
    """List all pending partition change recommendations."""
    pending = []
    for run_id, state in pending_states.items():
        if state.phase.value == "awaiting_approval":
            pending.append({
                "run_id": run_id,
                "recommendations": [r.model_dump() for r in state.recommendations]
            })
    return {"pending": pending}

@router.post("/approve/{run_id}")
async def approve_partition_change(run_id: str, request: ApprovalRequest):
    """Approve or reject a pending partition recommendation."""
    if run_id not in pending_states:
        raise HTTPException(status_code=404, detail=f"Run ID {run_id} not found")

    from app.agent.nodes.validation import apply_approval
    state = pending_states[run_id]
    state = apply_approval(state, request.approved, request.notes)
    pending_states[run_id] = state

    return {
        "run_id": run_id,
        "approved": request.approved,
        "phase": state.phase.value,
    }
