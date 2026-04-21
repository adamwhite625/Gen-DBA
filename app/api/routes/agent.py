"""Cac route API dieu khien Tac tu Gen-DBA."""
from fastapi import APIRouter

router = APIRouter()

@router.post("/analyze")
async def start_analysis():
    """Bat dau phan tich workload va dua ra khuyen nghi phan manh."""
    return {"message": "Analysis started", "status": "in_progress"}

@router.get("/status/{run_id}")
async def get_agent_status(run_id: str):
    """Lay trang thai hien tai cua mot phien chay tac tu."""
    return {"run_id": run_id, "phase": "reasoning", "progress": "50%"}
