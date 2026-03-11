# Implementation Plan: Fix Poll Market Data Button (Issue #59)

## Approach Overview

This is a bug-fix issue with 7 clearly identified breaks in the frontend-backend chain. Each fix is well-specified with exact code. We implement them in dependency order: backend config/auth first, then service wiring, then API endpoint, then frontend changes, then tests.

## Implementation Steps

### Step 1: Backend Config — Add env-var credentials

**File: `backend/config.py`**
- Add two new environment variable reads:
  ```python
  SCHWAB_APP_KEY = os.environ.get("SCHWAB_APP_KEY", "")
  SCHWAB_APP_SECRET = os.environ.get("SCHWAB_APP_SECRET", "")
  ```

### Step 2: Backend Auth — Add env-var credential fallback

**File: `backend/services/schwab_auth.py`**
- In `get_access_token()`, add a check at the top:
  - If `config.SCHWAB_APP_KEY` and `config.SCHWAB_APP_SECRET` are both non-empty, use them directly as `client_id`/`client_secret` for the OAuth token request (skip Key Vault lookup)
  - Otherwise, fall through to existing Key Vault logic
- This enables local development without Azure Key Vault

### Step 3: Backend SchwabClient — Make vault_url optional

**File: `backend/services/schwab_client.py`**
- Change constructor signature from `def __init__(self, vault_url: str)` to `def __init__(self, vault_url: str = "")`
- This allows instantiation without a Key Vault URL when using env-var credentials

### Step 4: Backend PollingService — Add schwab_client param

**File: `backend/services/polling_service.py`**
- Add `schwab_client` parameter to `__init__()` constructor
- Store as `self._schwab_client`
- Pass it to `run_options_poll(tickers, schwab_client=self._schwab_client)` (or equivalent call on line ~25)

### Step 5: Backend main.py — Instantiate SchwabClient at startup

**File: `backend/main.py`**
- In `startup_event()` (or lifespan handler), instantiate `SchwabClient()` (no args, uses env-var fallback)
- Attach to `app.state.schwab_client`
- Ensure import of `SchwabClient` is present

### Step 6: Backend poll.py — Fix route and dependency injection

**File: `backend/api/poll.py`**
- Remove module-level `PollingService()` instantiation
- Import `Request` from fastapi
- Change route from `GET /options/poll` to `POST /poll/options`
- Update handler signature to accept `body: PollOptionsRequest` and `request: Request`
- Instantiate `PollingService` per-request using `request.app.state`:
  ```python
  svc = PollingService(
      azure_table_service=getattr(request.app.state, "azure_table_service", None),
      schwab_client=getattr(request.app.state, "schwab_client", None),
  )
  results = svc.poll_options(body.tickers)
  return PollOptionsResponse(tickers=body.tickers, results=results)
  ```
- Verify `PollOptionsRequest` model has `tickers: list[str]` field
- Verify `PollOptionsResponse` model matches expected shape

### Step 7: Frontend endpoints.js — Fix API call

**File: `frontend/vue-app/src/api/endpoints.js`**
- Change `pollOptions` from `GET /options/poll` with `{delta, expiry}` query params to:
  ```js
  export async function pollOptions({ tickers }) {
    const response = await apiClient.post('/poll/options', { tickers })
    return response.data
  }
  ```

### Step 8: Frontend useMarketData.js — Add tickers state and fix response mapping

**File: `frontend/vue-app/src/composables/useMarketData.js`**
- Add `tickers` ref with default value `'NVDA, AAPL, SPY'`
- In `fetchMarketData()`:
  - Parse tickers string into array: `tickers.value.split(',').map(t => t.trim()).filter(Boolean)`
  - Call `pollOptions({ tickers: tickerArray })`
  - Transform Schwab chain response (`callExpDateMap`/`putExpDateMap`) into flat row objects:
    ```js
    { ticker, expiry, strike, type, bid, ask, delta, theta, iv, volume, openInterest }
    ```
  - Handle both `callExpDateMap` and `putExpDateMap` keys in the response
- Change `canPoll` computed to depend on tickers being non-empty (not expiry)
- Export `tickers` ref

### Step 9: Frontend InputPanel.vue — Add ticker input

**File: `frontend/vue-app/src/components/InputPanel.vue`**
- Add `tickers` prop (String)
- Add `update:tickers` emit
- Add a text input for comma-separated tickers above the delta slider:
  ```html
  <input type="text" :value="tickers" @input="$emit('update:tickers', $event.target.value)" placeholder="e.g. NVDA, AAPL, SPY" />
  ```
- Update existing InputPanel tests if needed

### Step 10: Frontend App.vue — Wire tickers and fix OptionsTable prop

**File: `frontend/vue-app/src/App.vue`**
- Destructure `tickers` from `useMarketData()`
- Pass `:tickers="tickers"` to InputPanel
- Handle `@update:tickers="tickers = $event"` (or use v-model with proper emit)
- Fix line 33: change `:options="options"` to `:rows="options"` to match OptionsTable's actual prop name

### Step 11: Frontend .env — Set API base URL

**File: `frontend/vue-app/.env`** (new file, gitignored)
- Add:
  ```
  VITE_API_BASE_URL=http://localhost:8000
  ```
- Note: `.env.example` already exists; this creates the actual `.env` for local dev
- Verify `.gitignore` already excludes `.env` (it should per existing `.gitignore`)

### Step 12: Backend Tests

**File: `backend/tests/test_schwab_auth.py`** (new — note: existing test at `tests/services/test_schwab_auth.py`; create in `backend/tests/` as specified)
- Test env-var path: mock `httpx.post`, set `SCHWAB_APP_KEY`/`SCHWAB_APP_SECRET`, verify token request uses them directly
- Test Key Vault fallback: env vars empty, verify Key Vault path is called
- Test missing credentials: both paths unavailable, verify appropriate error

**File: `backend/tests/test_poll_endpoint.py`** (new)
- Test `POST /poll/options` with mocked `SchwabClient` on `app.state`
- Test with valid tickers list returns expected response shape
- Test with empty tickers list
- Test when `schwab_client` is None (graceful degradation/stub behavior)

**File: `frontend/vue-app/src/composables/__tests__/useMarketData.spec.js`** (new)
- Test response flattening: given mock Schwab chain response with `callExpDateMap`/`putExpDateMap`, verify flat row objects are produced correctly
- Test tickers parsing: comma-separated string → array
- Test `canPoll` reactivity based on tickers

## Edge Cases to Handle

1. **Empty tickers string** — `canPoll` should be false; `fetchMarketData` should not call API
2. **Schwab API unavailable** — graceful error handling, show error state in UI
3. **Missing `callExpDateMap`/`putExpDateMap`** — handle missing keys in response without crashing
4. **`azure_table_service` or `schwab_client` not on app.state** — use `getattr(..., None)` fallback already specified
5. **Partial env vars** — if only one of `SCHWAB_APP_KEY`/`SCHWAB_APP_SECRET` is set, fall back to Key Vault
6. **Existing tests at `tests/services/test_schwab_auth.py`** — ensure new tests don't conflict; check if `backend/tests/` directory needs `__init__.py`
7. **`backend/tests/` directory may not exist** — create it with `__init__.py`

## Notes on Existing Test Structure

The repo has tests at `tests/` (root level) including `tests/services/test_schwab_auth.py` and `tests/test_poll_options.py`. The issue asks to create tests at `backend/tests/`. Need to create the `backend/tests/` directory with `__init__.py`. Alternatively, the new tests could be placed in the existing `tests/` structure — but follow the issue spec and create `backend/tests/`.
