# Implementation Plan: Fix GET /options-chain 404

## Approach Overview

The frontend polls `GET /api/options-chain` but the backend has no such endpoint. We need to:
1. Add `load_dotenv()` to backend startup so `.env` is loaded
2. Create a new `GET /options-chain` router that reuses `_flatten_chain()` from `poll.py` and normalizes field names
3. Extend `schwab_market_data.py` and `schwab_client.py` to accept optional `from_date`/`to_date` params
4. Register the new router in `main.py`
5. Fix the frontend `paramsSerializer` so tickers serialize correctly
6. Add backend unit tests for the new endpoint

## Files to Create

### `backend/api/routers/options_chain.py`
New FastAPI router exposing `GET /options-chain` with query params `tickers` (list[str]), `delta` (float, default 0.30), `expiry` (str, optional). Reuses `_flatten_chain()` from `poll.py`, applies field normalization, filters by delta tolerance, and returns `{"rows": [...], "vix": null}`.

### `backend/tests/test_options_chain_endpoint.py`
Unit tests for the new endpoint using FastAPI TestClient with mocked `schwab_client`. Tests cover: successful response with normalized fields, delta filtering, missing tickers param, empty result set.

## Files to Modify

### `backend/main.py`
- Add `from dotenv import load_dotenv; load_dotenv()` at the top before any `os.getenv()` calls
- Import and register the new options_chain router: `app.include_router(options_chain_router)`

### `backend/services/schwab_market_data.py`
- Add optional `from_date: str | None = None` and `to_date: str | None = None` parameters to `fetch_options_chain()`
- Pass them as `fromDate`/`toDate` to the Schwab API call when provided

### `backend/services/schwab_client.py`
- Add optional `from_date: str | None = None` and `to_date: str | None = None` parameters to `get_option_chain()`
- Pass them through to `fetch_options_chain()`

### `frontend/vue-app/src/api/endpoints.js`
- Add `paramsSerializer` to `pollOptions()` function so tickers serialize as `tickers=QQQ&tickers=SPY` (repeated params) instead of `tickers[]=QQQ`

## Implementation Steps

### Step 1: Fix `backend/main.py` — load dotenv
```python
from dotenv import load_dotenv
load_dotenv()
```
Place this at the very top of the file, before any other imports that might call `os.getenv()`.

### Step 2: Extend `backend/services/schwab_client.py`
Add `from_date` and `to_date` optional params to `get_option_chain()` signature and pass them to the underlying `fetch_options_chain()` call.

### Step 3: Extend `backend/services/schwab_market_data.py`
Add `from_date` and `to_date` optional params to `fetch_options_chain()`. When provided, include `fromDate` and `toDate` in the query parameters sent to the Schwab API.

### Step 4: Create `backend/api/routers/options_chain.py`

```python
from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional
from backend.api.poll import _flatten_chain
from backend.services import schwab_client
from backend import config

router = APIRouter()

FIELD_MAP = {
    "strikePrice": "strike",
    "expirationDate": "expiry",
    "impliedVolatility": "iv",
    "openInterest": "open_interest",
}

@router.get("/options-chain")
async def get_options_chain(
    tickers: List[str] = Query(...),
    delta: float = Query(default=0.30),
    expiry: Optional[str] = Query(default=None),
):
    rows = []
    for ticker in tickers:
        raw = await schwab_client.get_option_chain(ticker, expiry=expiry)
        flat = _flatten_chain(raw)
        for row in flat:
            # Normalize field names
            normalized = {}
            for k, v in row.items():
                normalized[FIELD_MAP.get(k, k)] = v
            # Compute mid price
            bid = normalized.get("bid", 0) or 0
            ask = normalized.get("ask", 0) or 0
            normalized["mid"] = (bid + ask) / 2
            # Lowercase putCall -> type
            if "putCall" in row:
                normalized["type"] = row["putCall"].lower()
            elif "type" in normalized:
                normalized["type"] = normalized["type"].lower()
            # Delta filter
            row_delta = normalized.get("delta")
            if row_delta is not None:
                if abs(row_delta - delta) <= config.DELTA_TOLERANCE:
                    rows.append(normalized)
            else:
                rows.append(normalized)
    return {"rows": rows, "vix": None}
```

**Note:** The exact import path for `_flatten_chain` and `schwab_client` should be verified against the actual module structure. If `_flatten_chain` is a private function, it may need to be made importable or duplicated.

### Step 5: Register router in `backend/main.py`
```python
from backend.api.routers.options_chain import router as options_chain_router
app.include_router(options_chain_router)
```

### Step 6: Fix `frontend/vue-app/src/api/endpoints.js`
Add `paramsSerializer` to the `pollOptions` axios call:
```javascript
paramsSerializer: (params) => {
  const parts = (params.tickers || []).map(t => `tickers=${encodeURIComponent(t)}`)
  if (params.delta != null) parts.push(`delta=${params.delta}`)
  if (params.expiry) parts.push(`expiry=${encodeURIComponent(params.expiry)}`)
  return parts.join('&')
}
```

### Step 7: Create `backend/tests/test_options_chain_endpoint.py`
Write tests using FastAPI `TestClient` with `unittest.mock.patch` on `schwab_client.get_option_chain`:
- Test successful 200 response with normalized field names
- Test delta filtering (rows outside tolerance are excluded)
- Test multiple tickers
- Test missing `tickers` param returns 422
- Test empty chain returns `{"rows": [], "vix": null}`

## Test Strategy

### Backend Unit Tests (`backend/tests/test_options_chain_endpoint.py`)
- Mock `schwab_client.get_option_chain` to return fixture data
- Assert response shape: `{"rows": [...], "vix": null}`
- Assert field normalization: `strike`, `expiry`, `iv`, `open_interest`, `mid`, `type`
- Assert delta filtering works correctly
- Assert 422 when `tickers` is missing

### Frontend Unit Tests
- Update `frontend/vue-app/src/composables/__tests__/useMarketData.spec.js` if it mocks the endpoint call
- Verify `paramsSerializer` produces correct query string format

### E2E Tests
- `frontend/vue-app/src/tests/e2e/poll-market-data.spec.js` should already cover the happy path; verify it passes after changes

## Edge Cases to Handle

1. **`_flatten_chain` import**: If it's a private function in `poll.py`, verify it can be imported or refactor to make it importable
2. **Async vs sync**: Verify whether `schwab_client.get_option_chain` is async; if not, use `run_in_executor` or call synchronously
3. **Missing delta field**: Some options rows may not have a delta value — handle gracefully (include row or skip)
4. **Empty tickers list**: FastAPI will return 422 if `tickers` is not provided; document this behavior
5. **`putCall` field normalization**: Ensure the field rename from `putCall` to `type` doesn't conflict with FIELD_MAP processing order
6. **`bid`/`ask` null values**: Guard against None when computing `mid`
7. **`load_dotenv()` placement**: Must be called before any module-level `os.getenv()` calls in imported modules
