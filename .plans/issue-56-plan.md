# Implementation Plan: RESTful API Refactor (Issue #56)

## Approach Overview

There is exactly one non-RESTful endpoint to fix: the existing `POST /poll/options` endpoint, where `/poll` is a verb rather than a resource. The fix is to rename it to `GET /options-chain`. This is a pure URL structure and HTTP method correction — no response shape changes, no versioning, no other endpoints are in scope.

Before writing code, we will read the relevant files to confirm the exact current route signature and to produce a complete list of all other existing endpoints (for awareness, not modification).

---

## Pre-Work: Endpoint Audit

Read the following files before making any changes:

- `backend/api/poll.py`
- `backend/api/routers/trades.py`
- `backend/api/routers/health.py`
- `backend/main.py`

**Goal:** Produce a full list of all current endpoints and their HTTP methods. Only `POST /poll/options` is being changed in this issue. All other endpoints are documented here for reference and left untouched.

---

## Files to Modify

### Backend

#### `backend/api/poll.py`
- Change the route decorator from `@router.post("/poll/options")` (or equivalent) to `@router.get("/options-chain")`.
- Move any request body parameters to query parameters in the function signature, since GET requests do not carry a request body.

#### `backend/models/poll.py`
- If the existing model is used as a POST request body, assess whether its fields should become individual query parameters on the new GET endpoint. Update accordingly.

#### `backend/main.py`
- If the router from `poll.py` is registered with a prefix of `/poll`, update or remove that prefix so the final resolved path is `/options-chain`.

### Frontend

#### `frontend/vue-app/src/api/endpoints.js`
- Update the endpoint constant referencing `/poll/options` to `/options-chain`.

#### `frontend/vue-app/src/api/client.js`
- Change `axios.post(...)` to `axios.get(...)` for this endpoint.
- Move any request body fields to query parameters.

#### `frontend/vue-app/src/composables/useMarketData.js`
- Update the call site to use the new URL and pass parameters as query params instead of a request body.

### Tests

#### `tests/test_poll_options.py`
- Update the test URL from `/poll/options` to `/options-chain`.
- Change the HTTP method from POST to GET.
- Update any request body assertions to query parameter assertions.

#### `frontend/vue-app/src/components/__tests__/InputPanel.spec.js`
- Update mocked API calls to reference the new endpoint URL and GET method.

#### `frontend/vue-app/src/components/__tests__/OptionsTable.spec.js`
- Same as above if this component triggers the options-chain fetch.

---

## Files Confirmed Not in Scope

- `backend/api/routers/trades.py` — Audit for awareness only; no changes unless the audit reveals it contains the `/poll/options` route instead of `poll.py`.
- `backend/api/routers/health.py` — Audit for awareness only; no changes expected.
- `tests/test_trades_router.py` — No changes unless the audit shows the polled route lives in `trades.py`.

---

## Implementation Steps

1. **Audit current routes** — Read `backend/api/poll.py`, `backend/api/routers/trades.py`, `backend/api/routers/health.py`, and `backend/main.py`. Produce a complete list of all endpoints and their HTTP methods. Confirm the exact location of the `POST /poll/options` route.
2. **Update backend route** — Change the decorator to `@router.get("/options-chain")` and convert request body parameters to query parameters.
3. **Update router registration** — Fix the prefix in `backend/main.py` if needed so the resolved path is `/options-chain`.
4. **Update model** — Adjust `backend/models/poll.py` if the model needs to change from a request body schema to query parameter fields.
5. **Update frontend endpoint constant** — Change the URL in `endpoints.js`.
6. **Update frontend HTTP method and parameter style** — Update `client.js` and `useMarketData.js` to use GET and query params.
7. **Update backend tests** — Update `test_poll_options.py` for the new URL, method, and parameter style.
8. **Update frontend tests** — Update component specs that mock this API call.
9. **Smoke test** — Run the app end-to-end to confirm the options chain loads correctly with the new endpoint.

---

## Edge Cases to Handle

- **Query parameter encoding** — If the old POST body contained arrays (e.g., multiple tickers), confirm a consistent serialization format for query params (e.g., `?ticker=AAPL&ticker=TSLA` or `?tickers=AAPL,TSLA`) and apply it consistently across backend and frontend.
- **CORS preflight** — Verify existing CORS middleware handles the new GET route correctly.
- **Caching** — GET endpoints are cacheable by default. If the options chain is time-sensitive, add `Cache-Control: no-store` to the response to prevent stale data.

---

## Test Strategy

- **Backend unit** — `tests/test_poll_options.py`: call `GET /options-chain` with query params via the FastAPI test client and assert the correct response.
- **Frontend unit** — Vitest specs in `src/components/__tests__/`: mock `GET /options-chain` and assert components render correctly.
- **Integration** — Run the FastAPI test client against the full app to confirm routing resolves to the correct handler.
- **E2E smoke** — Manually verify the Vue frontend loads options chain data after the change.