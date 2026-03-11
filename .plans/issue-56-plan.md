# Implementation Plan: RESTful API Refactor (Issue #56)

## Approach Overview

The only confirmed non-RESTful endpoint is `POST /poll/options` (or similar), where `/poll` is a verb, not a resource. The fix is to rename it to `GET /options-chain`. This is a pure URL + HTTP method correction with no response shape changes. Both the backend router and the frontend API client/endpoints must be updated together.

Before writing code we need to confirm the exact current route signature by reading the relevant files, but based on the repo structure the changes are well-bounded.

---

## Files to Modify

### Backend

#### `backend/api/poll.py`
- Currently defines the polling logic (likely a POST handler on `/poll/options` or similar).
- Change the HTTP method to `GET` and rename the path to `/options-chain`.
- Remove any request-body parameters that should instead be query parameters (since GET requests use query params, not a body).

#### `backend/api/routers/trades.py`
- Inspect for any routes that use verb-based naming (e.g., `/poll`, `/analyze`, `/fetch`).
- Rename any such routes to noun-based resource paths.
- Confirm HTTP verbs are semantically correct (GET for reads, POST for creates, PUT/PATCH for updates, DELETE for deletes).

#### `backend/api/routers/health.py`
- Inspect for any non-RESTful patterns (likely fine, but confirm).

#### `backend/main.py`
- Update router prefix registrations if the prefix `/poll` is registered here — change to `/options-chain` or remove the prefix if the path is now fully specified in the router.

#### `backend/models/poll.py`
- If the model is used as a request body for the old POST endpoint, assess whether it should become query parameters for the new GET endpoint. Update accordingly.

### Frontend

#### `frontend/vue-app/src/api/endpoints.js`
- Update the endpoint constant(s) referencing `/poll/options` (or similar) to `/options-chain`.

#### `frontend/vue-app/src/api/client.js`
- If the HTTP method is hardcoded here (e.g., `axios.post(...)`), change to `axios.get(...)`.
- Move any request body fields to query parameters.

#### `frontend/vue-app/src/composables/useMarketData.js`
- Update any call sites that reference the old endpoint or pass a request body — convert to query params.

### Tests

#### `tests/test_poll_options.py`
- Update test URLs from `/poll/options` to `/options-chain`.
- Change HTTP method from POST to GET.
- Update any request body assertions to query parameter assertions.

#### `tests/test_trades_router.py`
- Update any test routes that were renamed in `trades.py`.

#### `frontend/vue-app/src/components/__tests__/InputPanel.spec.js`
- Update mocked API calls to use the new endpoint and GET method.

#### `frontend/vue-app/src/components/__tests__/OptionsTable.spec.js`
- Same as above if this component triggers the options-chain fetch.

---

## Implementation Steps

1. **Audit current routes** — Read `backend/api/poll.py`, `backend/api/routers/trades.py`, `backend/api/routers/health.py`, and `backend/main.py` to produce a complete list of current endpoints and their HTTP methods.
2. **Identify all non-RESTful patterns** — Flag any verb-in-URL routes or incorrect HTTP methods beyond the known `/poll/options` case.
3. **Update backend: rename `/poll/options` → `GET /options-chain`**
   - Change route decorator from `@router.post("/poll/options")` to `@router.get("/options-chain")`.
   - Move request body fields to query parameters in the function signature.
   - Update the router prefix in `main.py` if needed.
4. **Update backend: fix any other non-RESTful routes in `trades.py`** — Based on audit findings.
5. **Update frontend: `endpoints.js`** — Change the URL constant.
6. **Update frontend: `client.js` / `useMarketData.js`** — Change HTTP method and parameter passing style.
7. **Update all backend tests** — `test_poll_options.py`, `test_trades_router.py`.
8. **Update all frontend tests** — Component specs that mock the API.
9. **Manual smoke test** — Run the app end-to-end to confirm the options chain loads correctly.

---

## Edge Cases to Handle

- **Query parameter encoding**: If the old POST body contained complex objects (e.g., arrays of tickers), ensure they are properly serialized as query params (e.g., `?ticker=AAPL&ticker=TSLA` or `?tickers=AAPL,TSLA`).
- **CORS preflight**: GET requests with custom headers may still trigger CORS preflight — verify middleware is not broken.
- **Caching**: GET endpoints are cacheable by default; ensure no unintended caching occurs if the options chain is time-sensitive (add `Cache-Control: no-store` if needed).
- **Other verb-named routes**: The audit in step 1 may reveal additional routes in `trades.py` (e.g., `/poll`, `/analyze`) that also need renaming.

---

## Test Strategy

- **Unit**: Update `tests/test_poll_options.py` to call `GET /options-chain` with query params and assert correct response.
- **Unit**: Update `tests/test_trades_router.py` for any renamed trade routes.
- **Frontend unit**: Update Vitest specs in `src/components/__tests__/` to mock the new endpoint.
- **Integration**: Run the FastAPI test client against the full app to confirm routing resolves correctly.
- **E2E smoke**: Manually verify the Vue frontend loads options chain data after the change.
