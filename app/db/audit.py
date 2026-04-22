from datetime import datetime
from pydantic import BaseModel, Field

class AuditEntry(BaseModel):
    """Record of a DDL operation executed by the agent."""
    run_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    table_name: str
    operation: str  # e.g., 'ALTER_PARTITION'
    ddl_script: str
    backup_ddl: str
    success: bool
    error_message: str = ""
    approved_by: str = "human"
    approval_notes: str = ""

# In-memory audit log (replace with DB table or file storage in production)
audit_log: list[AuditEntry] = []

def record_audit(entry: AuditEntry):
    """Append a new record to the audit trail and log it."""
    from app.logger import logger
    audit_log.append(entry)
    
    # Also log via structured logger
    logger.info(
        f"Audit: {entry.operation} on {entry.table_name}. Success: {entry.success}", 
        extra={"run_id": entry.run_id, "audit_data": entry.model_dump()}
    )

def get_audit_history(limit: int = 50) -> list[dict]:
    """Retrieve recent audit entries."""
    return [entry.model_dump() for entry in audit_log[-limit:]]
