# Gen-DBA: AI-Driven Data Partitioning Agent for Oracle 19c

An intelligent database administration agent that uses **LangGraph** and **OpenAI GPT-4o** to analyze Oracle workload patterns and automatically recommend optimal data partitioning strategies.

Built as a capstone project for the **Distributed Database Systems** course at VNUHCM - University of Information Technology.

---

## Architecture

```
                    +------------------+
                    |   FastAPI (API)   |
                    +--------+---------+
                             |
                    +--------v---------+
                    |  LangGraph Agent  |
                    +--------+---------+
                             |
          +------------------+------------------+
          |          |           |               |
   +------v--+ +----v-----+ +--v--------+ +----v------+
   |Perception| |Reasoning | |Validation | |  Action   |
   |  Node    | |  Node    | |   Node    | |   Node    |
   +------+---+ +----+-----+ +--+--------+ +----+------+
          |          |           |               |
   +------v----------v-----------v---------------v------+
   |              Oracle Database 19c                    |
   |         V$SQL | DBA_TABLES | EXPLAIN PLAN           |
   +----------------------------------------------------+
```

**Agent Pipeline:**

1. **Perception** - Collects workload data from Oracle `V$SQLAREA` and `DBA_TABLES`
2. **Reasoning** - Sends workload summary to OpenAI for partition strategy analysis
3. **Validation** - Validates the generated DDL syntax and safety
4. **Action** - Executes DDL with backup, audit logging, and partition pruning verification
5. **Evaluation** - Verifies execution results and gathers post-change statistics

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Agent Framework | LangGraph 1.1 |
| LLM | OpenAI GPT-4o-mini |
| Backend API | FastAPI + Uvicorn |
| Database | Oracle Database 19c Enterprise Edition |
| DB Driver | python-oracledb (Thin mode) |
| Configuration | Pydantic Settings + dotenv |
| Logging | Structured JSON (file + console) |
| Containerization | Docker + Docker Compose |
| Benchmark | TPC-H queries + matplotlib |

---

## Project Structure

```
gen-dba/
|-- app/
|   |-- agent/
|   |   |-- nodes/          # LangGraph pipeline nodes
|   |   |   |-- perception.py
|   |   |   |-- reasoning.py
|   |   |   |-- validation.py
|   |   |   |-- action.py
|   |   |   |-- evaluation.py
|   |   |-- prompts/         # LLM prompt templates
|   |   |-- graph.py         # LangGraph workflow definition
|   |   |-- state.py         # Agent state schema
|   |-- api/
|   |   |-- routes/
|   |   |   |-- agent.py     # /api/agent/* endpoints
|   |   |   |-- partitions.py # /api/partitions/* endpoints
|   |   |   |-- metrics.py   # /api/metrics/* endpoints
|   |   |-- error_handler.py # Global exception handlers
|   |-- db/
|   |   |-- oracle_client.py # Oracle connection and query execution
|   |   |-- ddl_manager.py   # Safe DDL execution with backup
|   |   |-- audit.py         # Audit trail for DDL operations
|   |   |-- queries.py       # SQL query definitions
|   |-- config.py            # Application settings
|   |-- logger.py            # Structured JSON logger
|   |-- main.py              # FastAPI application entry point
|-- scripts/
|   |-- benchmark.py              # Benchmark runner
|   |-- benchmark_queries.py      # TPC-H query definitions
|   |-- run_all_benchmarks.py     # Full 3-scenario benchmark suite
|   |-- visualize_results.py      # Chart generation from results
|   |-- setup_db_user.py          # Oracle user setup
|   |-- test_pipeline.py          # Agent pipeline test
|-- tests/
|   |-- test_oracle_connection.py # Oracle connection unit tests
|-- docs/
|   |-- EVALUATION_REPORT.md      # Performance evaluation report
|-- benchmark_charts/             # Generated charts (PNG)
|-- Dockerfile
|-- docker-compose.yml
|-- requirements.txt
|-- .env.example
```

---

## Prerequisites

- **Python 3.11+** (via Anaconda recommended)
- **Oracle Database 19c** Enterprise Edition with Partitioning option
- **Docker Desktop** (optional, for containerized deployment)
- **OpenAI API Key** with access to GPT-4o-mini

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/adamwhite625/Gen-DBA.git
cd Gen-DBA
```

### 2. Create conda environment

```bash
conda create -n gendba python=3.11 -y
conda activate gendba
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
# Edit .env with your Oracle credentials and OpenAI API key
```

### 4. Set up Oracle database user

```bash
python -m scripts.setup_db_user
```

This creates the `GENDBA` user with necessary privileges (`SELECT ANY DICTIONARY`, `ALTER SYSTEM`, etc.) and loads TPC-H sample data.

### 5. Ensure Oracle PDB is open

```sql
-- Connect as SYSDBA
ALTER PLUGGABLE DATABASE ALL OPEN;
```

---

## Usage

### Run the API server

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

API docs available at: `http://localhost:8000/docs`

### Run with Docker

```bash
docker-compose up -d --build
```

### Key API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/agent/analyze` | Trigger workload analysis |
| POST | `/api/partitions/approve/{run_id}` | Approve partition recommendations |
| POST | `/api/agent/execute/{run_id}` | Execute approved DDL |
| GET | `/api/metrics/performance` | View top queries and table sizes |
| GET | `/api/metrics/partitions/summary` | View partition layout |
| GET | `/api/metrics/audit` | View DDL audit trail |
| GET | `/api/metrics/health/oracle` | Check Oracle connection |

---

## Running Benchmarks

### Full benchmark suite (3 scenarios)

```bash
python -m scripts.run_all_benchmarks
```

This runs Baseline, Static Partition, and Gen-DBA Optimized scenarios sequentially with cache flushing between rounds.

### Generate charts

```bash
python -m scripts.visualize_results
```

Charts are saved to `benchmark_charts/`.

### Run unit tests

```bash
python -m tests.test_oracle_connection
```

---

## Benchmark Results Summary

| Comparison | Avg Change | Best Query |
|------------|-----------|------------|
| Gen-DBA vs Static Partition | **-10.4% faster** | Q14: -41.5% |
| Gen-DBA vs Baseline | +12.3% (expected on small dataset) | Q6: -23.3% |

> On small datasets (TPC-H SF=0.01), partition management overhead exceeds pruning benefits vs. heap tables. Gen-DBA's advantage over static partitioning confirms that AI-driven strategy selection outperforms manual rules. Benefits increase with data scale.

Full evaluation report: [docs/EVALUATION_REPORT.md](docs/EVALUATION_REPORT.md)

---

## References

1. Arpaci-Dusseau, R. H. (2018). *Operating Systems: Three Easy Pieces* - Chapter on Data Partitioning
2. Oracle Corporation. *Oracle Database VLDB and Partitioning Guide, 19c*
3. Pavlo, A. et al. (2021). *Make Your Database System Dream of Electric Sheep: Towards Self-Driving Database Management Systems*
4. LangGraph Documentation - https://langchain-ai.github.io/langgraph/

---

## License

This project is developed for academic purposes as part of the Distributed Database Systems course at UIT-VNUHCM.
