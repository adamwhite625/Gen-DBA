"""Structured JSON logging configuration for the Gen-DBA agent."""
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    """Format log records as JSON for structured logging."""

    def format(self, record):
        """Convert a log record into a JSON-formatted string."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "module": record.module,
            "function": record.funcName,
            "message": record.getMessage(),
        }
        if hasattr(record, "run_id"):
            log_entry["run_id"] = record.run_id
        if hasattr(record, "phase"):
            log_entry["phase"] = record.phase
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)

def setup_logger(name: str = "gendba") -> logging.Logger:
    """Configure and return the application logger."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        console = logging.StreamHandler()
        console.setFormatter(JSONFormatter())
        logger.addHandler(console)

        file_handler = logging.FileHandler("gendba_audit.log")
        file_handler.setFormatter(JSONFormatter())
        logger.addHandler(file_handler)

    return logger

logger = setup_logger()
