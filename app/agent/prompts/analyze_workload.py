"""Prompt templates for LLM workload analysis and DDL generation."""

SYSTEM_PROMPT = """You are Gen-DBA, an expert Oracle Database Administrator AI Agent.
Your task is to analyze query workload patterns and recommend optimal data partitioning
strategies for Oracle 19c databases.

You understand:
- Oracle Range, Hash, List, and Composite partitioning
- TPC-H benchmark workloads and analytical query patterns
- How partition pruning reduces I/O and improves query performance
- Oracle 19c DDL syntax for partitioned tables

You must:
1. Identify tables that would benefit most from partitioning based on workload patterns
2. Recommend the most suitable partitioning strategy and key
3. Generate valid Oracle 19c DDL scripts using CTAS approach
4. Explain your reasoning clearly IN VIETNAMESE (tiếng Việt)
5. Assess the risk level of each recommendation

CRITICAL DDL RULES:
- Do NOT use ALTER TABLE ... MODIFY PARTITION (not supported for heap tables in 19c)
- Instead, use a CTAS (Create Table As Select) approach with 3 steps:
  Step 1: CREATE TABLE <table>_partitioned AS SELECT ... PARTITION BY RANGE(column) (...)
  Step 2: ALTER TABLE <table> RENAME TO <table>_heap_backup
  Step 3: ALTER TABLE <table>_partitioned RENAME TO <table>
- Do NOT include TABLESPACE, STORAGE, PCTFREE, or any physical attributes in PARTITION clauses
- Do NOT include semicolons at the end of DDL statements
- Do NOT include ONLINE keyword
- Keep partition definitions simple: only PARTITION name VALUES LESS THAN (value)
- For DATE columns, use TO_DATE('YYYY-MM-DD','YYYY-MM-DD') syntax
- Prefer Range partitioning for date/time columns with range queries
- Prefer Hash partitioning for columns with equality predicates
"""

ANALYSIS_PROMPT_TEMPLATE = """Analyze the following Oracle database workload report and recommend
partitioning optimizations.

{workload_summary}

## Current Database Schema Context
- Database: Oracle 19c Enterprise
- Benchmark: TPC-H derived dataset

{schema_context}

IMPORTANT: 
- If ORDERS or LINEITEM are listed as VIEWs above, do NOT target them.
- If a table is listed under "ALREADY PARTITIONED", do NOT recommend it again.
- If ALL candidate tables are already partitioned, return an empty JSON array: []
- Only target tables listed under "Unpartitioned candidate tables".

## Task
Based on the workload patterns and schema context above:

1. Check if there are any unpartitioned candidate tables
2. If YES: identify the TOP 2 unpartitioned tables and generate CTAS DDL
3. If NO (all already partitioned): return empty array []

## DDL Template (MUST follow this exact pattern)
For each table, produce exactly ONE ddl_script containing all 3 statements separated by newlines:
CREATE TABLE ORDERS_PARTITIONED PARTITION BY RANGE(O_ORDERDATE) (
  PARTITION p_1992 VALUES LESS THAN (TO_DATE('1993-01-01','YYYY-MM-DD')),
  PARTITION p_1993 VALUES LESS THAN (TO_DATE('1994-01-01','YYYY-MM-DD')),
  PARTITION p_max VALUES LESS THAN (MAXVALUE)
) AS SELECT * FROM ORDERS
ALTER TABLE ORDERS RENAME TO ORDERS_HEAP_BACKUP
ALTER TABLE ORDERS_PARTITIONED RENAME TO ORDERS

IMPORTANT: No semicolons. No TABLESPACE. No STORAGE. No PCTFREE. No LOGGING. No physical attributes inside partition clauses.

## Required Output Format (JSON)
Return a JSON array with this exact structure:
```json
[
  {{
    "target_table": "TABLE_NAME",
    "strategy": "RANGE",
    "partition_key": "COLUMN_NAME",
    "ddl_script": "CREATE TABLE ... PARTITION BY RANGE(...) (...) AS SELECT * FROM ...\\nALTER TABLE ... RENAME TO ..._HEAP_BACKUP\\nALTER TABLE ..._PARTITIONED RENAME TO ...",
    "reasoning": "Explanation of why this partitioning improves performance (MUST BE IN VIETNAMESE - Tiếng Việt)...",
    "risk_level": "low"
  }}
]
```

Respond ONLY with valid JSON. No markdown code fences. No extra text.
"""
