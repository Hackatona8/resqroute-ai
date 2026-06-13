# ResQRoute AI

Autonomous, data-driven transit engine for perishable logistics. ResQRoute AI ingests simulated IoT telemetry, estimates spoilage risk, recalculates transit paths under dynamic congestion and thermal conditions, and emits flash-intervention decisions for localized stock absorption.

## Architecture

- `config/`: application settings and risk thresholds.
- `src/api/`: FastAPI routers and Pydantic request/response models.
- `src/engine/`: telemetry processing and route optimization.
- `src/agents/`: deterministic agent decision logic and prompt templates.
- `tests/`: API and routing validation.

## Stack

- Python 3.11+
- FastAPI
- Pandas
- NetworkX
- LangChain-compatible agent layer
- Pytest

## Development flow

The repository is structured for a staged build:

1. `init/setup` establishes the skeleton and project metadata.
2. `feature/telemetry-pipeline` adds ingestion and spoilage risk processing.
3. `feature/dynamic-routing` adds dynamic graph path recalculation.
4. `feature/agentic-intervention` adds structured flash-intervention decisions.

## Local setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Run the API once implementation is in place:

```bash
uvicorn src.main:app --reload
```

Run the deterministic end-to-end demo harness:

```bash
python -m src.main --demo
```
