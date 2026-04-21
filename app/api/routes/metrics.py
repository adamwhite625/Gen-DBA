"""Cac route API cho chi so hieu nang va benchmarking."""
from fastapi import APIRouter

router = APIRouter()

@router.get("/workload")
async def get_workload_metrics():
    """Lay cac chi so hieu nang workload tu V$SQL."""
    return {"top_sql": [], "message": "Metrics collection in Phase 4"}

@router.get("/compare")
async def compare_performance():
    """So sanh hieu nang truoc va sau khi phan manh."""
    return {"improvement": "N/A", "message": "Benchmarking in Phase 4"}
