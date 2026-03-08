# Implementation Plan: Epic 5 — Tradability Index Engine

## Approach Overview

This epic introduces a scoring and ranking layer on top of existing options data stored in Azure Table Storage. We will:
1. Add a `TradabilityService` that extracts metrics, computes scores, and ranks candidates.
2. Add a `TradesRouter` exposing `GET /trades/best`.
3. Add configurable weights to `config.py`.
4. Write unit tests for each story.

The existing `azure_table_service.py` already handles reads from `optionsdata`; we will reuse it directly.

---

## Files to Create

### `backend/services/tradability_service.py`
Core service implementing Stories 5.1, 5.2, and 5.3:
- `extract_metrics(row: dict) -> dict` — pulls `delta`, `theta`, `iv`, `premium` from a table row
- `compute_score(metrics: dict, weights: TradabilityWeights) -> float` — applies the weighted formula
- `rank_candidates(rows: list[dict], weights: TradabilityWeights) -> list[dict]` — scores and sorts all rows
- `get_best_trade(rows: list[dict], weights: TradabilityWeights) -> dict | None` — returns top-ranked row

### `backend/api/routers/trades.py`
FastAPI router:
- `GET /trades/best` — fetches all rows from `optionsdata` table, calls `TradabilityService.get_best_trade()`, returns the result or 404 if no candidates exist.

### `backend/models/tradability.py`
Pydantic models:
- `TradabilityWeights` — holds `theta_weight`, `iv_weight`, `premium_weight`, `delta_risk_weight` with defaults
- `TradabilityScore` — response model with all option fields plus computed `score`

### `tests/services/test_tradability_service.py`
Unit tests for metric extraction, score computation, and ranking.

### `tests/test_trades_router.py`
Integration tests for `GET /trades/best`.

---

## Files to Modify

### `backend/config.py`
Add tradability weight configuration:
```python
THETA_WEIGHT: float = 1.0
IV_WEIGHT: float = 1.0
PREMIUM_WEIGHT: float = 1.0
DELTA_RISK_WEIGHT: float = 1.0
```
These can be overridden via environment variables.

### `backend/main.py`
Register the new `trades` router:
```python
from backend.api.routers import trades
app.include_router(trades.router, prefix="/trades", tags=["trades"])
```

### `backend/api/routers/__init__.py`
Export the new trades router if needed.

### `backend/requirements.txt`
No new dependencies expected; confirm `pydantic` and `fastapi` versions are sufficient.

---

## Implementation Steps

### Step 1 — Models (`backend/models/tradability.py`)
```python
from pydantic import BaseModel

class TradabilityWeights(BaseModel):
    theta_weight: float = 1.0
    iv_weight: float = 1.0
    premium_weight: float = 1.0
    delta_risk_weight: float = 1.0

class TradabilityScore(BaseModel):
    symbol: str
    delta: float
    theta: float
    iv: float
    premium: float
    score: float
    raw: dict  # full original row for traceability
```

### Step 2 — Config (`backend/config.py`)
Add weight fields with env-var support so weights are tunable without code changes.

### Step 3 — Tradability Service (`backend/services/tradability_service.py`)

```python
from backend.models.tradability import TradabilityWeights, TradabilityScore

def extract_metrics(row: dict) -> dict:
    """Extract required metric fields from an optionsdata table row."""
    return {
        "delta": float(row.get("delta", 0.0)),
        "theta": float(row.get("theta", 0.0)),
        "iv": float(row.get("iv", 0.0)),
        "premium": float(row.get("premium", 0.0)),
    }

def compute_score(metrics: dict, weights: TradabilityWeights) -> float:
    """Apply the tradability scoring formula."""
    return (
        (weights.theta_weight * metrics["theta"])
        + (weights.iv_weight * metrics["iv"])
        + (weights.premium_weight * metrics["premium"])
        - (weights.delta_risk_weight * abs(metrics["delta"] - 0.30))
    )

def rank_candidates(
    rows: list[dict],
    weights: TradabilityWeights,
) -> list[TradabilityScore]:
    """Score and rank all candidate rows, highest score first."""
    scored = []
    for row in rows:
        metrics = extract_metrics(row)
        score = compute_score(metrics, weights)
        scored.append(
            TradabilityScore(
                symbol=row.get("RowKey", ""),
                score=score,
                raw=row,
                **metrics,
            )
        )
    return sorted(scored, key=lambda x: x.score, reverse=True)

def get_best_trade(
    rows: list[dict],
    weights: TradabilityWeights,
) -> TradabilityScore | None:
    """Return the highest-scored trade candidate, or None if no rows."""
    ranked = rank_candidates(rows, weights)
    return ranked[0] if ranked else None
```

### Step 4 — Trades Router (`backend/api/routers/trades.py`)

```python
from fastapi import APIRouter, HTTPException, Depends
from backend.services.azure_table_service import AzureTableService
from backend.services.tradability_service import get_best_trade
from backend.models.tradability import TradabilityScore, TradabilityWeights
from backend.config import settings

router = APIRouter()

@router.get("/best", response_model=TradabilityScore)
async def get_best_trade_endpoint():
    """Return the highest-scored trade candidate from stored options data."""
    service = AzureTableService()
    rows = await service.get_all_options()  # adjust to actual method name
    weights = TradabilityWeights(
        theta_weight=settings.THETA_WEIGHT,
        iv_weight=settings.IV_WEIGHT,
        premium_weight=settings.PREMIUM_WEIGHT,
        delta_risk_weight=settings.DELTA_RISK_WEIGHT,
    )
    best = get_best_trade(rows, weights)
    if best is None:
        raise HTTPException(status_code=404, detail="No trade candidates available")
    return best
```

### Step 5 — Register Router (`backend/main.py`)
Add:
```python
from backend.api.routers import trades
app.include_router(trades.router, prefix="/trades", tags=["trades"])
```

### Step 6 — Tests
Write unit and integration tests (see Test Strategy below).

---

## Test Strategy

### Unit Tests — `tests/services/test_tradability_service.py`

1. **`test_extract_metrics_happy_path`** — row with all four fields returns correct float dict
2. **`test_extract_metrics_missing_fields`** — missing fields default to 0.0
3. **`test_extract_metrics_string_values`** — string numerics are cast to float
4. **`test_compute_score_formula`** — known inputs produce expected score (manual calculation)
5. **`test_compute_score_delta_penalty`** — delta far from 0.30 reduces score
6. **`test_rank_candidates_ordering`** — list of rows returns sorted descending by score
7. **`test_rank_candidates_empty`** — empty list returns empty list
8. **`test_get_best_trade_returns_top`** — returns highest-scored item
9. **`test_get_best_trade_empty`** — returns None for empty input

### Integration Tests — `tests/test_trades_router.py`

1. **`test_get_best_trade_success`** — mock AzureTableService returns rows; endpoint returns 200 with TradabilityScore
2. **`test_get_best_trade_no_data`** — mock returns empty list; endpoint returns 404
3. **`test_get_best_trade_response_schema`** — response contains `symbol`, `score`, `delta`, `theta`, `iv`, `premium`

---

## Edge Cases to Handle

1. **Missing metric fields** — rows missing `delta`, `theta`, `iv`, or `premium` should default to `0.0` rather than raising a `KeyError`.
2. **Non-numeric field values** — fields stored as strings (common in Azure Table Storage) must be cast to `float`.
3. **Empty options table** — `GET /trades/best` must return HTTP 404 with a clear message.
4. **Single candidate** — ranking with one row should return that row as the best.
5. **Tied scores** — when two rows have identical scores, ordering is stable (first encountered wins).
6. **Negative theta/premium** — formula handles negative values correctly; no clamping applied unless specified.
7. **Weight configuration** — all weights default to `1.0`; zero weights are valid (effectively ignoring that metric).
