"""Agent state schema and data models for the LangGraph pipeline."""
from typing import Optional, List
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

class AgentPhase(str, Enum):
    IDLE = "idle"
    PERCEIVING = "perceiving"
    REASONING = "reasoning"
    AWAITING_APPROVAL = "awaiting_approval"
    EXECUTING = "executing"
    EVALUATING = "evaluating"
    COMPLETED = "completed"
    FAILED = "failed"

class WorkloadEntry(BaseModel):
    sql_id: str
    sql_text: str
    executions: int
    elapsed_time_ms: float
    buffer_gets: int
    disk_reads: int

class PartitionRecommendation(BaseModel):
    target_table: str
    strategy: str  # e.g., 'RANGE', 'HASH', 'LIST'
    partition_key: str
    ddl_script: str
    reasoning: str
    risk_level: str = "medium"

class PerformanceSnapshot(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.now)
    avg_query_latency_ms: float = 0.0
    total_buffer_gets: int = 0
    total_disk_reads: int = 0
    total_elapsed_time_ms: float = 0.0
    query_count: int = 0

class AgentState(BaseModel):
    run_id: str = ""
    phase: AgentPhase = AgentPhase.IDLE
    workload_entries: List[WorkloadEntry] = []
    recommendations: List[PartitionRecommendation] = []
    is_approved: Optional[bool] = None
    executed_ddl: List[str] = []
    error_message: str = ""
    before_snapshot: Optional[PerformanceSnapshot] = None
    after_snapshot: Optional[PerformanceSnapshot] = None
    improvement_report: str = ""
