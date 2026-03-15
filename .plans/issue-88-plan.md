# Implementation Plan: Backend Refactor — Issue #88 (Revised)

## Approach Overview

This refactor touches services, models, routers, and tests across the backend. The work is purely structural — no new business logic is introduced. We will:

1. Audit existing code before creating new files
2. Create new consolidated service files
3. Create new per-model files
4. Update all routers to use new services/models
5. Update all tests to use new import paths
6. Delete old files only after all consumers are verified

Order matters: audit first, create new files, update consumers, verify no broken imports, then delete old files.

---

## Pre-Work: Audit Before Touching Anything

Before writing a single line of new code, complete the following audits and record findings:

### Audit A: `market_data_service.py`
- List every function/class defined
- List every caller across the entire codebase (services, agents, routers, tests)
- Mark each function as **dead** (no callers) or **live** (has callers)
- For live functions: decide whether they move to `SchwabService` or stay temporarily
- **Do not delete this file until all live callers are migrated**

### Audit B: Agent files
Inspect all files under `backend/agents/`:
- `options_data_agent.py`
- `tradability_agent.py`
- `metrics_agent.py`
- `workflow.py`
- `state.py`
- Any other files present

For each file, record:
- Every import from old service/model paths
- Every import from old model paths
- Whether the file uses `market_data_service`, `schwab_auth`, `schwab_client`, `schwab_market_data`, `schwab_filters`, `tradability_service`, `ccp_calculator`, or any old model file

### Audit C: Frontend API calls
Inspect all frontend files for calls to:
- `POST /poll/options`
- `GET /trades/best`
- `POST /trades/calculate`
- Any other endpoints being removed or renamed

Files to check at minimum:
- `BestTradeCard.vue`
- `endpoints.js`
- Any other `.vue`, `.js`, or `.ts` files that reference API endpoints

Record every file and line that must change.

### Audit D: Wildcard imports
Search the entire codebase for `from backend.models import *` or `from models import *`. Record every file using wildcard imports so `models/__init__.py` re-exports are verified to be complete.

### Audit E: Circular import risk
Before creating new consolidated files, map the import graph for:
- `SchwabService` (will it import anything that imports it back?)
- `TradesComparisonService` (same check)
- New model files (do any models import from services?)

Document the dependency graph and confirm no cycles exist before proceeding.

---

## Step 1: Create `SchwabService`

### New file: `backend/services/schwab_service.py`

Consolidate all Schwab-related logic:
- **From `schwab_auth.py`**: credential resolution, token fetch (`get_access_token()`)
- **From `schwab_client.py`**: auth wrapper, chain fetch with token refresh (`fetch_options_chain()`)
- **From `schwab_market_data.py`**: raw HTTP calls to Schwab `/marketdata/chains`
- **From `schwab_filters.py`**: filter contracts by expiry/delta (`filter_contracts()`)
- **From `market_data_service.py`**: only functions confirmed **live** and not covered above (per Audit A)

Public interface:
```python
class SchwabService:
    def get_access_token(self) -> str: ...
    def fetch_options_chain(self, symbol: str, **kwargs) -> dict: ...
    def filter_contracts(self, chain: dict, **kwargs) -> list: ...
```

### Validation checkpoint
Before moving to Step 2:
- [ ] `SchwabService` is importable in isolation with no import errors
- [ ] All methods have unit tests passing (see Step 7)
- [ ] No circular imports detected

---

## Step 2: Create `TradesComparisonService`

### New file: `backend/services/trades_comparison_service.py`

Consolidate trade scoring logic:
- **From `tradability_service.py`**: `rank_candidates()`, `compute_score()`, `extract_metrics()`
- **From `ccp_calculator.py`**: `compute_annualized_roi()`, `compute_days_to_expiration()`, `enrich_put_options_with_roi()`

Public interface:
```python
class TradesComparisonService:
    def rank_candidates(self, contracts: list) -> list: ...
    def compute_score(self, contract: dict) -> float: ...
    def extract_metrics(self, contract: dict) -> dict: ...
    def compute_annualized_roi(self, **kwargs) -> float: ...
    def compute_days_to_expiration(self, **kwargs) -> int: ...
    def enrich_put_options_with_roi(self, contracts: list) -> list: ...
```

### Validation checkpoint
Before moving to Step 3:
- [ ] `TradesComparisonService` is importable in isolation with no import errors
- [ ] All methods have unit tests passing (see Step 7)
- [ ] No circular imports detected

---

## Step 3: Reorganize Models

Create individual model files split from `options_data.py`, `poll.py`, and `tradability.py`.

### New files:
- `backend/models/options_contract.py` — `OptionsContractRecord`
- `backend/models/options_chain_request.py` — `OptionsChainRequest`
- `backend/models/options_chain_response.py` — `OptionsChainResponse` (renamed from `PollOptionsResponse`)
- `backend/models/tradability_score.py` — `TradabilityScore`
- `backend/models/tradability_metrics.py` — `TradabilityMetrics`

### Keep unchanged:
- `backend/models/run_log.py` — `RunLogRecord`

### Update `backend/models/__init__.py`
Re-export **all** models from new locations. This must include every model previously exported so that any wildcard imports (identified in Audit D) continue to work without modification.

```python
# backend/models/__init__.py
from backend.models.options_contract import OptionsContractRecord
from backend.models.options_chain_request import OptionsChainRequest
from backend.models.options_chain_response import OptionsChainResponse
from backend.models.tradability_score import TradabilityScore
from backend.models.tradability_metrics import TradabilityMetrics
from backend.models.run_log import RunLogRecord
# Add any additional models identified in Audit D
```

### Validation checkpoint
Before moving to Step 4:
- [ ] Each new model file is importable independently
- [ ] `from backend.models import *` resolves all previously available names
- [ ] No circular imports between model files and service files

---

## Step 4: Redesign `/trades` API

### Modify `backend/api/routers/trades.py`
- **Remove** `GET /trades/best`
- **Remove** `POST /trades/calculate`
- **Add** `GET /trades` — fetches options data via `SchwabService`, runs `TradesComparisonService.rank_candidates()`, returns flat list of all trades with tradability scores
- Import from `TradesComparisonService` and `SchwabService`
- Use `TradabilityScore` and `TradabilityMetrics` models for response

Response shape:
```json
[
  {
    "symbol": "...",
    "strike": 100.0,
    "expiration": "2024-03-15",
    "tradability_index": 0.87
  }
]
```

### Validation checkpoint
- [ ] `GET /trades` returns expected response shape in integration test
- [ ] `GET /trades/best` returns 404
- [ ] `POST /trades/calculate` returns 404

---

## Step 5: Hide `POST /poll/options`

### Modify `backend/api/poll.py`
- Remove the `POST /poll/options` route handler
- Keep `_flatten_chain` as an internal utility function — **do not delete it**; it may be used by other internal callers
- Ensure no router registration of this endpoint in `main.py`

### Validation checkpoint
- [ ] `POST /poll/options` returns 404
- [ ] `_flatten_chain` is still importable for internal use
- [ ] No other file that calls `_flatten_chain` is broken

---

## Step 6: Update All Consumers

Complete all consumer updates before deleting any old files. Work through consumers in dependency order: agents first, then services, then routers, then `main.py`.

### 6a: Update agent files (identified in Audit B)
For each agent file with old imports:
- `options_data_agent.py` — replace old service/model imports
- `tradability_agent.py` — replace old service/model imports
- `metrics_agent.py` — replace old service/model imports
- `workflow.py` — replace old service/model imports if any
- `state.py` — replace old service/model imports if any

After each file update, run its existing tests to confirm no regressions before continuing.

### 6b: Update `backend/services/polling_service.py`
- Replace scattered Schwab imports with `SchwabService`

### 6c: Update `backend/api/routers/options_chain.py`
- Replace imports from `schwab_auth`, `schwab_client`, `schwab_market_data`, `schwab_filters` with `SchwabService`
- Replace imports from `tradability_service`, `ccp_calculator` with `TradesComparisonService`
- Update model imports to new file locations

### 6d: Update `backend/main.py`
- Remove import and registration of `poll` router's `/poll/options` route
- Update any direct service imports to use `SchwabService`

### 6e: Update frontend (identified in Audit C)
- Update `endpoints.js` and any `.vue` files calling removed endpoints
- Replace calls to `POST /poll/options`, `GET /trades/best`, `POST /trades/calculate` with new endpoints
- Confirm frontend builds without errors after changes

### Validation checkpoint
Before moving to Step 7:
- [ ] `grep -r "schwab_auth\|schwab_client\|schwab_market_data\|schwab_filters\|tradability_service\|ccp_calculator\|market_data_service" backend/` returns no results outside of the old files themselves and Step 8's deletion list
- [ ] `grep -r "from backend.models.options_data\|from backend.models.poll\|from backend.models.tradability" .` returns no results outside of the old model files themselves
- [ ] All existing passing tests still pass

---

## Step 7: Update Tests

Update tests after new files exist and consumers are updated, but **before** deleting old files so tests can be run against both old and new code during transition.

### Tests to update:

| Old test file | Action | What to test |
|---|---|---|
| `tests/services/test_schwab_auth.py` | Update imports | `SchwabService.get_access_token()` |
| `tests/services/test_schwab_filters.py` | Update imports | `SchwabService.filter_contracts()` |
| `tests/services/test_schwab_market_data.py` | Update imports | `SchwabService` HTTP methods |
| `tests/services/test_ccp_calculator.py` | Update imports | `TradesComparisonService` ROI methods |
| `tests/services/test_tradability_service.py` | Update imports | `TradesComparisonService` scoring methods |
| `tests/services/test_market_data_service.py` | Audit then delete or repurpose | Only delete if all covered by `SchwabService` tests |
| `tests/test_trades_router.py` | Rewrite | `GET /trades` flat list with scores; 404 for old endpoints |
| `tests/test_poll_options.py` | Update | Verify `POST /poll/options` returns 404 |
| `tests/test_options_data_model.py` | Update imports | New model file locations |
| `tests/test_project_structure.py` | Update expected layout | New file structure |
| `backend/tests/test_schwab_auth.py` | Update imports | `SchwabService` |
| `backend/tests/test_poll_endpoint.py` | Update | Removed endpoint returns 404 |
| `backend/tests/test_options_chain_endpoint.py` | Update imports | New service/model paths |
| `tests/agents/test_options_data_agent.py` | Update imports | Agent still works with new imports |
| `tests/agents/test_tradability_agent.py` | Update imports | Agent still works with new imports |

### New tests to add:
- `tests/services/test_schwab_service.py` — full coverage of `SchwabService` public interface
- `tests/services/test_trades_comparison_service.py` — full coverage of `TradesComparisonService` public interface
- `tests/models/test_model_imports.py` — assert each model file is independently importable and `__init__.py` exports are complete

### Validation checkpoint
- [ ] All tests pass with zero failures
- [ ] No test imports from old file paths
- [ ] Coverage for `SchwabService` and `TradesComparisonService` is at least equal to combined coverage of the files they replace

---

## Step 8: Delete Old Files

**Only delete a file after:**
1. All its callers have been updated (verified by grep in Step 6 checkpoint)
2. All its tests have been updated or replaced (verified in Step 7)
3. The full test suite passes without it

Delete in this order to catch any missed dependencies early:

1. `backend/services/schwab_filters.py`
2. `backend/services/schwab_auth.py`
3. `backend/services/schwab_client.py`
4. `backend/services/schwab_market_data.py`
5. `backend/services/market_data_service.py` ← only after Audit A confirms all live code migrated
6. `backend/services/tradability_service.py`
7. `backend/services/ccp_calculator.py`
8. `backend/models/options_data.py`
9. `backend/models/poll.py`
10. `backend/models/tradability.py`

After each deletion, run the full test suite. If any test fails, stop and resolve before continuing.

---

## Post-Refactor API Surface

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /health | Health check |
| GET | /options-chain | Live options chain from Schwab (filtered, enriched with CCP ROI) |
| GET | /trades | All trades with tradability index (frontend sorts/filters) |

### Endpoints that must return 404 after refactor:
| Method | Endpoint |
|--------|----------|
| POST | /poll/options |
| GET | /trades/best |
| POST | /trades/calculate |

---

## Test Strategy

1. **Unit tests** — Each method in `SchwabService` and `TradesComparisonService` tested in isolation with mocks
2. **Integration tests** — `GET /trades` returns expected shape; `GET /options-chain` still works end-to-end
3. **Regression tests** — `POST /poll/options`, `GET /trades/best`, and `POST /trades/calculate` all return 404
4. **Model tests** — Each model file importable independently; `__init__.py` exports verified; no circular imports
5. **Structure test** — `test_project_structure.py` updated to assert new file layout and absence of deleted files
6. **Agent tests** — All agent files function correctly after import path updates
7. **Frontend smoke test** — Frontend builds and API calls resolve correctly after endpoint updates

---

## Edge Cases and Risk Mitigations

| Risk | Mitigation |
|---|---|
| `_flatten_chain` accidentally deleted | Explicitly marked as internal utility; kept in `poll.py`; verified by test that it remains importable |
| `market_data_service.py` has live callers not yet identified | Audit A must complete before Step 1; file stays until all callers migrated |
| Wildcard imports break after model reorganization | Audit D identifies all wildcard import sites; `__init__.py` re-exports verified complete before old model files deleted |
| Agent files (`workflow.py`, `state.py