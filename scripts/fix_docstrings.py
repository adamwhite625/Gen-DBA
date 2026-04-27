"""Add missing module docstrings to all Python files in the project."""
import os

FILES_DOCSTRINGS = {
    'app/agent/graph.py': '"""LangGraph workflow definition for the Gen-DBA agent pipeline."""',
    'app/agent/state.py': '"""Agent state schema and data models for the LangGraph pipeline."""',
    'app/agent/nodes/action.py': '"""Action node: executes approved DDL scripts with backup and audit."""',
    'app/agent/nodes/evaluation.py': '"""Evaluation node: verifies execution results and gathers post-change stats."""',
    'app/agent/nodes/perception.py': '"""Perception node: collects workload data from Oracle V$SQL."""',
    'app/agent/nodes/reasoning.py': '"""Reasoning node: invokes LLM to analyze workload and generate recommendations."""',
    'app/agent/nodes/validation.py': '"""Validation node: validates DDL syntax and safety before execution."""',
    'app/api/error_handler.py': '"""Global exception handlers for the FastAPI application."""',
    'app/api/routes/agent.py': '"""API routes for triggering and managing the Gen-DBA agent."""',
    'app/api/routes/metrics.py': '"""API routes for performance metrics, benchmarking, and audit trail."""',
    'app/api/routes/partitions.py': '"""API routes for partition management and approval workflow."""',
    'app/db/audit.py': '"""Audit trail storage for all DDL operations executed by the agent."""',
    'app/db/ddl_manager.py': '"""Safe DDL execution manager with backup and partition pruning verification."""',
    'app/db/oracle_client.py': '"""Oracle database client for executing SQL and DDL commands."""',
}

for filepath, docstring in FILES_DOCSTRINGS.items():
    with open(filepath, 'r') as f:
        content = f.read()
    if not content.startswith('"""'):
        content = docstring + '\n' + content
        with open(filepath, 'w') as f:
            f.write(content)
        print(f'  Added docstring: {filepath}')
    else:
        print(f'  Already has: {filepath}')

# Fix __init__ docstring in oracle_client.py
with open('app/db/oracle_client.py', 'r') as f:
    content = f.read()
old = '    def __init__(self):\n        self.params'
new = '    def __init__(self):\n        """Initialize Oracle connection parameters and configure Thin mode."""\n        self.params'
if old in content and '"""Initialize Oracle' not in content:
    content = content.replace(old, new)
    with open('app/db/oracle_client.py', 'w') as f:
        f.write(content)
    print('  Added __init__ docstring: app/db/oracle_client.py')

print('\nDone!')
