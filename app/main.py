"""Diem vao ung dung FastAPI cho he thong Tac tu Gen-DBA."""
from fastapi import FastAPI
from app.api.routes import agent, partitions, metrics
import oracledb
from app.api.error_handler import oracle_error_handler

app = FastAPI(
    title="Gen-DBA API",
    description="He thong Tac tu AI tu dong toi uu phan manh du lieu Oracle 19c",
    version="0.1.0"
)

app.add_exception_handler(oracledb.DatabaseError, oracle_error_handler)

# Dang ky cac route
app.include_router(agent.router, prefix="/api/agent", tags=["Agent"])
app.include_router(partitions.router, prefix="/api/partitions", tags=["Partitions"])
app.include_router(metrics.router, prefix="/api/metrics", tags=["Metrics"])

@app.get("/")
async def root():
    """Endpoint goc de kiem tra API."""
    return {
        "message": "Gen-DBA Database Agent API is running",
        "docs": "/docs",
        "status": "healthy"
    }

@app.get("/health")
async def health_check():
    """Kiem tra suc khoe cua API va ket noi Oracle."""
    from app.db.oracle_client import oracle_client
    db_status = oracle_client.test_connection()
    return {"status": "healthy", "database": db_status}
