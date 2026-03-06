# Implementation Plan: Story 1.2 – Define Project Directory Structure

## Approach
Scaffold the full directory layout as specified in the issue tasks. Each Python package directory gets an `__init__.py` (which also satisfies the .gitkeep requirement). Non-Python directories (frontend, infra subdirs) get `.gitkeep` files. A `backend/requirements.txt` is created with initial dependencies appropriate for a FastAPI + LangGraph options trading agent.

The existing top-level `.gitkeep` files in `backend/`, `frontend/`, and `infra/` can be removed once real content exists in those directories.

## Files to Create

### Backend Python Packages (with `__init__.py`)
- `backend/api/__init__.py` — FastAPI route handlers package
- `backend/agents/__init__.py` — LangGraph agents package (MarketSentimentAgent, OptionsDataAgent, MetricsAgent, TradabilityAgent)
- `backend/services/__init__.py` — Business logic package (options fetcher, tradability engine)
- `backend/models/__init__.py` — Pydantic models / data schemas package

### Frontend
- `frontend/vue-app/.gitkeep` — Placeholder for Vue frontend application

### Infrastructure
- `infra/terraform/.gitkeep` — Placeholder for Terraform/Bicep scripts for AKS + Azure Table Storage

### Backend Dependencies
- `backend/requirements.txt` — Initial Python dependencies

## Files to Modify / Remove
- `backend/.gitkeep` — Remove (replaced by real package structure)
- `frontend/.gitkeep` — Remove (replaced by vue-app subdirectory)
- `infra/.gitkeep` — Remove (replaced by infra subdirectory)

## Implementation Steps

1. **Create backend Python package directories** with `__init__.py` files:
   - `backend/api/__init__.py` (empty or with docstring)
   - `backend/agents/__init__.py` (empty or with docstring)
   - `backend/services/__init__.py` (empty or with docstring)
   - `backend/models/__init__.py` (empty or with docstring)

2. **Create frontend placeholder**:
   - `frontend/vue-app/.gitkeep`

3. **Create infra placeholder**:
   - `infra/terraform/.gitkeep` (or `infra/bicep/.gitkeep` — see notes)

4. **Create `backend/requirements.txt`** with initial dependencies:
   ```
   fastapi>=0.110.0
   uvicorn[standard]>=0.29.0
   langgraph>=0.1.0
   langchain>=0.1.0
   pydantic>=2.0.0
   httpx>=0.27.0
   python-dotenv>=1.0.0
   azure-data-tables>=12.5.0
   ```

5. **Remove stale `.gitkeep` files** at top-level backend/, frontend/, infra/ once subdirectories are populated.

## Test Strategy
- No unit tests required for directory scaffolding
- CI/smoke check: verify all expected paths exist (can be a simple shell script or pytest path-existence test)
- Verify `backend/requirements.txt` is parseable: `pip install -r backend/requirements.txt --dry-run`

## Edge Cases
- The issue mentions "Terraform or Bicep" — create a single placeholder unless CLAUDE.md specifies one; default to `infra/terraform/` or keep at `infra/` level
- Ensure `__init__.py` files are truly empty or contain only a module docstring to avoid import side effects
- The existing `backend/.gitkeep`, `frontend/.gitkeep`, `infra/.gitkeep` should be deleted to keep the repo clean
