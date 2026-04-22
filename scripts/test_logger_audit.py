import time
from app.logger import logger
from app.db.audit import AuditEntry, record_audit, get_audit_history

def test_logging_and_audit():
    print("1. Testing JSON Logger...")
    logger.info("This is a test log message from the test script.", extra={"run_id": "test-123", "phase": "testing"})
    print("Check gen-dba/gendba_audit.log to verify the JSON format.\n")

    print("2. Testing Audit Log...")
    entry = AuditEntry(
        run_id="test-run-456",
        table_name="TEST_TABLE",
        operation="TEST_OPERATION",
        ddl_script="ALTER TABLE TEST_TABLE ADD COLUMN test_col VARCHAR2(10);",
        backup_ddl="CREATE TABLE TEST_TABLE (id NUMBER);",
        success=True
    )
    
    record_audit(entry)
    
    history = get_audit_history()
    print(f"Retrieved {len(history)} audit records.")
    if history:
        print("Latest audit record:")
        print(history[-1])

if __name__ == "__main__":
    test_logging_and_audit()
