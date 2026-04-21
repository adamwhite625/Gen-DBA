"""Cac route API quan ly va hien thi phan manh."""
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def list_partitions():
    """Liet ke tat ca cac bang va phan manh hien tai trong schema."""
    return {"tables": ["ORDERS", "LINEITEM"], "partitions_found": 0}

@router.post("/approve/{task_id}")
async def approve_recommendation(task_id: str):
    """Phe duyet mot khuyen nghi phan manh tu AI."""
    return {"task_id": task_id, "status": "approved", "message": "DDL will be executed"}
