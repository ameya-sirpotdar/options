# Implementation Plan: POST /trades/score Endpoint

## Approach

The scoring logic already exists in `backend/services/tradability_service.py`. This issue is primarily about wiring up a new POST endpoint that accepts options data directly (rather than reading from Azure Table Storage) and returning ranked candidates. The frontend just needs its URL updated to match.

**Dependency Note:** Issue #73 (field name normalization) may affect field names (`iv`, `premium`) expected by `extract_metrics()`. This implementation should be compatible with normalized field names. If #73 is not yet merged, document the field name requirement clearly in the endpoint docstring.

---

## Files to Modify

### 1. `backend/api/routers/trades.py`
- Add `ScoreRequest` Pydantic model with fields: `options: List[Dict[str, Any]]`, `delta: float = 0.30`, `expiry: str = ""`, `vix: Optional[float] = None`
- Add `POST /score` endpoint that calls `rank_candidates(body.options)` and returns `{"best_trade": ranked[0], "ranked_candidates": ranked}`
- Raise `HTTPException(status_code=404, detail="No valid trade candidates")` if ranked list is empty
- Add necessary imports: `List`, `Dict`, `Any`, `Optional` from typing; `BaseModel` from pydantic; `rank_candidates` from tradability_service

### 2. `frontend/vue-app/src/api/endpoints.js`
- Update `calculateTrades` function URL from `/trades/calculate` to `/trades/score`
- Verify payload shape matches `{ options, delta, expiry, vix }` — adjust if needed

---

## Files to Create

### 3. `backend/tests/test_score_trades_endpoint.py`
- Test `POST /trades/score` with valid options array → 200 with `best_trade` and `ranked_candidates`
- Test with empty options array → 404
- Test with options missing required fields → verify graceful handling
- Test response shape: `best_trade` is a dict, `ranked_candidates` is a list
- Use FastAPI `TestClient`

---

## Implementation Steps

1. **Inspect existing code** — review `backend/api/routers/trades.py` for current imports and router setup; review `backend/services/tradability_service.py` to confirm `rank_candidates()` signature and what fields `extract_metrics()` expects (`iv`, `premium`).

2. **Update `backend/api/routers/trades.py`**:
   ```python
   from typing import List, Dict, Any, Optional
   from pydantic import BaseModel
   from fastapi import APIRouter, HTTPException
   from backend.services.tradability_service import rank_candidates

   class ScoreRequest(BaseModel):
       options: List[Dict[str, Any]]
       delta: float = 0.30
       expiry: str = ""
       vix: Optional[float] = None

   @router.post("/score")
   def score_trades(body: ScoreRequest):
       """Score and rank options candidates.
       
       Expects options with normalized field names: 'iv' and 'premium'
       (as produced by the /options-chain endpoint after issue #73).
       """
       ranked = rank_candidates(body.options)
       if not ranked:
           raise HTTPException(status_code=404, detail="No valid trade candidates")
       return {"best_trade": ranked[0], "ranked_candidates": ranked}
   ```

3. **Update `frontend/vue-app/src/api/endpoints.js`**:
   - Find the `calculateTrades` function
   - Change URL from `/trades/calculate` to `/trades/score`
   - Confirm payload is `{ options, delta, expiry, vix }`

4. **Write tests in `backend/tests/test_score_trades_endpoint.py`**:
   - Use `TestClient` from `fastapi.testclient`
   - Import the FastAPI app from `backend/main.py`
   - Create sample options dicts with `iv`, `premium`, and other fields expected by `extract_metrics()`
   - Cover: happy path, empty list → 404, malformed options

5. **Run existing tests** — ensure `tests/test_trades_router.py` still passes after adding the new endpoint.

---

## Test Strategy

### Unit / Integration Tests (`backend/tests/test_score_trades_endpoint.py`)
- **Happy path**: POST with 2–3 valid option dicts → 200, response has `best_trade` (dict) and `ranked_candidates` (non-empty list)
- **Empty options**: POST `{"options": []}` → 404 with detail "No valid trade candidates"
- **Single option**: POST with one valid option → 200, `best_trade` equals `ranked_candidates[0]`
- **Missing optional fields**: POST without `delta`/`expiry`/`vix` → uses defaults, returns 200
- **Response shape**: assert `best_trade` and `ranked_candidates` keys present in response JSON

### Frontend Tests
- Update `frontend/vue-app/src/composables/__tests__/useMarketData.spec.js` if it mocks the `calculateTrades` endpoint URL
- Verify the mock URL matches `/trades/score`

### E2E (optional)
- `frontend/vue-app/src/tests/e2e/poll-market-data.spec.js` — verify Calculate Trades button flow reaches the correct endpoint

---

## Edge Cases

1. **Field name mismatch**: If #73 is not merged, options from the frontend may use different field names than `iv`/`premium`. The endpoint should document this dependency clearly. Consider adding a note or a field-name normalization step inside the endpoint if #73 is delayed.
2. **rank_candidates returns None vs empty list**: Verify whether `rank_candidates()` returns `None` or `[]` on no valid candidates — handle both cases in the null check.
3. **Large options arrays**: No pagination needed for MVP, but worth noting.
4. **vix field**: Currently accepted but may not be used by `rank_candidates()` — pass through or ignore gracefully.
