# Implementation Plan: Backend Refactor — Issue #88

## Approach Overview

This refactor touches services, models, routers, and tests across the backend. The work is purely structural — no new business logic is introduced. We will:

1. Create new consolidated service files
2. Create new per-model files
3. Update all routers to use new services/models
4. Update all tests to use new import paths
5. Delete old files

Order matters: create new files first, update consumers, then delete old files.

---

## Step 1: Create `SchwabService`

### New file: `backend/services/schwab_service.py`

Consolidate all Schwab-related logic:
- **From `schwab_auth.py`**: credential resolution, token fetch (`get_access_token()`)
- **From `schwab_client.py`**: auth wrapper, chain fetch with token refresh (`fetch_options_chain()`)
- **From `schwab_market_data.py`**: raw HTTP calls to Schwab `/marketdata/chains`
- **From `schwab_filters.py`**: filter contracts by expiry/delta (`filter_contracts()`)
- **From `market_data_service.py`**: legacy orchestrator logic (absorb any non-dead code, then discard)

Public interface:
```python
class SchwabService:
    def get_access_token(self) -> str: ...
    def fetch_options_chain(self, symbol: str, ...) -> dict: ...
    def filter_contracts(self, chain: dict, ...) -> list: ...
```

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
    def compute_annualized_roi(self, ...) -> float: ...
    def compute_days_to_expiration(self, ...) -> int: ...
    def enrich_put_options_with_roi(self, contracts: list) -> list: ...
```

---

## Step 3: Reorganize Models

Create individual model files (split from `options_data.py`, `poll.py`, `tradability.py`):

### New files:
- `backend/models/options_contract.py` — `OptionsContractRecord`
- `backend/models/options_chain_request.py` — `OptionsChainRequest`
- `backend/models/options_chain_response.py` — `OptionsChainResponse` (renamed from `PollOptionsResponse`)
- `backend/models/tradability_score.py` — `TradabilityScore`
- `backend/models/tradability_metrics.py` — `TradabilityMetrics`

### Keep unchanged:
- `backend/models/run_log.py` — `RunLogRecord`

### Update `backend/models/__init__.py`
Export all models from new locations.

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
    "tradability_index": 0.87,
    ...
  }
]
```

---

## Step 5: Hide `POST /poll/options`

### Modify `backend/api/poll.py`
- Remove the `POST /poll/options` route handler
- Keep `_flatten_chain` as an internal utility function (not exposed)
- Ensure no router registration of this endpoint in `main.py`

---

## Step 6: Update All Consumers

### Modify `backend/main.py`
- Remove import/registration of `poll` router's `/poll/options` route
- Update any direct service imports to use `SchwabService`

### Modify `backend/api/routers/options_chain.py`
- Replace imports from `schwab_auth`, `schwab_client`, `schwab_market_data`, `schwab_filters` with `SchwabService`
- Replace imports from `tradability_service`, `ccp_calculator` with `TradesComparisonService`
- Update model imports to new file locations

### Modify `backend/services/polling_service.py`
- Replace scattered Schwab imports with `SchwabService`

### Modify `backend/agents/` files as needed
- `options_data_agent.py`, `tradability_agent.py`, `metrics_agent.py` — update imports

---

## Step 7: Update Tests

### Tests to update (import paths):
- `tests/services/test_schwab_auth.py` → test `SchwabService.get_access_token()`
- `tests/services/test_schwab_filters.py` → test `SchwabService.filter_contracts()`
- `tests/services/test_schwab_market_data.py` → test `SchwabService` HTTP methods
- `tests/services/test_ccp_calculator.py` → test `TradesComparisonService` ROI methods
- `tests/services/test_tradability_service.py` → test `TradesComparisonService` scoring methods
- `tests/services/test_market_data_service.py` → delete or repurpose
- `tests/test_trades_router.py` → update to test `GET /trades` (flat list with scores)
- `tests/test_poll_options.py` → verify `POST /poll/options` returns 404
- `tests/test_options_data_model.py` → update imports to new model files
- `tests/test_project_structure.py` → update expected file structure
- `backend/tests/test_schwab_auth.py` → update imports
- `backend/tests/test_poll_endpoint.py` → update for removed endpoint
- `backend/tests/test_options_chain_endpoint.py` → update imports
- `tests/agents/test_options_data_agent.py` → update imports
- `tests/agents/test_tradability_agent.py` → update imports

---

## Step 8: Delete Old Files

Files to delete after all consumers are updated:
- `backend/services/schwab_auth.py`
- `backend/services/schwab_client.py`
- `backend/services/schwab_market_data.py`
- `backend/services/schwab_filters.py`
- `backend/services/market_data_service.py`
- `backend/services/tradability_service.py`
- `backend/services/ccp_calculator.py`
- `backend/models/tradability.py`
- `backend/models/poll.py`
- `backend/models/options_data.py`

---

## Post-Refactor API Surface

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /health | Health check |
| GET | /options-chain | Live options chain from Schwab (filtered, enriched with CCP ROI) |
| GET | /trades | All trades with tradability index (frontend sorts/filters) |

---

## Test Strategy

1. **Unit tests** — Each method in `SchwabService` and `TradesComparisonService` tested in isolation with mocks
2. **Integration tests** — `GET /trades` returns expected shape; `GET /options-chain` still works
3. **Regression tests** — `POST /poll/options` returns 404; old endpoints `GET /trades/best` and `POST /trades/calculate` return 404
4. **Model tests** — Each model file importable independently; no circular imports
5. **Structure test** — `test_project_structure.py` updated to assert new file layout

---

## Edge Cases

- Ensure `_flatten_chain` in `poll.py` is not accidentally deleted — keep as internal utility
- `market_data_service.py` may have non-dead code used by agents — audit before deleting
- `models/__init__.py` must re-export all models to avoid breaking any wildcard imports
- Frontend `BestTradeCard.vue` and `endpoints.js` may call old endpoints — update frontend API client
- Agent files (`workflow.py`, `state.py`) may import from old service/model paths — audit all agent files
