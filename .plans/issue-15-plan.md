# Implementation Plan: Issue #15 — Charles Schwab Market Data Integration

## Approach Overview

We will build three tightly scoped modules under `backend/services/` that map directly to Stories 3.1–3.3:

1. **`schwab_auth.py`** — OAuth 2.0 client-credentials flow, token caching, and refresh logic. Credentials (Client ID, Client Secret) are fetched exclusively from Azure Key Vault via the `azure-keyvault-secrets` SDK.
2. **`schwab_market_data.py`** — Authenticated HTTP client that calls Schwab's `/marketdata/chains` endpoint for each configured ticker and returns raw contract data.
3. **`schwab_filters.py`** — Pure filtering functions that accept raw contract lists and return only weekly-expiration put contracts with delta in the range [0.25, 0.35] (centred on 0.30).

A thin `backend/services/market_data_service.py` orchestrator ties the three together and exposes a single public interface for the rest of the application.

All secrets are injected at runtime from Azure Key Vault; no credentials appear in code, environment files, or version control.

---

## Files to Create

### `backend/services/schwab_auth.py`
Handles:
- Fetching `SCHWAB_CLIENT_ID` and `SCHWAB_CLIENT_SECRET` from Azure Key Vault.
- Requesting an OAuth 2.0 access token from Schwab's token endpoint (`https://api.schwabapi.com/v1/oauth/token`) using the client-credentials grant.
- In-memory token caching with expiry tracking.
- `get_access_token()` public function that returns a valid bearer token, refreshing automatically when within 60 s of expiry.

### `backend/services/schwab_market_data.py`
Handles:
- `fetch_options_chain(ticker: str, token: str) -> dict` — calls `GET /marketdata/chains?symbol={ticker}&contractType=PUT&includeQuotes=TRUE` and returns the parsed JSON response.
- `fetch_all_chains(tickers: list[str]) -> dict[str, dict]` — iterates tickers, obtains a fresh token per batch, and aggregates results.
- HTTP error handling (4xx/5xx) with structured logging.

### `backend/services/schwab_filters.py`
Handles:
- `is_weekly_expiration(expiration_date: str) -> bool` — determines whether a contract expires on a Friday within the next 8 days (standard weekly definition).
- `filter_contracts(raw_chain: dict, delta_target: float = 0.30, delta_tolerance: float = 0.05) -> list[dict]` — returns put contracts where:
  - `putCall == "PUT"`
  - expiration is a weekly expiration
  - `abs(contract["delta"]) - delta_target <= delta_tolerance`
- Returns a flat list of matching contract dicts.

### `backend/services/market_data_service.py`
Orchestrator:
- `get_filtered_options(tickers: list[str]) -> dict[str, list[dict]]` — calls auth → fetch → filter pipeline and returns filtered contracts keyed by ticker.
- Intended entry point for agents and API routes.

### `backend/config.py`
- `KEY_VAULT_URL` — read from environment variable `AZURE_KEY_VAULT_URL` (the only env var needed; no secrets in env).
- `SCHWAB_TOKEN_URL` constant.
- `SCHWAB_CHAINS_BASE_URL` constant.
- `TICKERS` list (configurable, e.g. `["SPY", "QQQ"]`).

### `tests/services/__init__.py`
Empty init to make the test directory a package.

### `tests/services/test_schwab_auth.py`
Unit tests for auth module.

### `tests/services/test_schwab_market_data.py`
Unit tests for market data fetching.

### `tests/services/test_schwab_filters.py`
Unit tests for filtering logic.

### `tests/services/test_market_data_service.py`
Integration-style tests for the orchestrator (all external calls mocked).

---

## Files to Modify

### `backend/services/__init__.py`
- Export `market_data_service.get_filtered_options` for convenience imports.

### `backend/requirements.txt`
Add:
```
azure-keyvault-secrets>=4.7.0
azure-identity>=1.15.0
httpx>=0.27.0
pytest>=8.0.0
pytest-asyncio>=0.23.0
python-dateutil>=2.9.0
```

---

## Implementation Steps

### Step 1 — Configuration (`backend/config.py`)
1. Define `KEY_VAULT_URL = os.environ["AZURE_KEY_VAULT_URL"]`.
2. Define Schwab API constants.
3. Define default `TICKERS` list.

### Step 2 — Auth Service (`backend/services/schwab_auth.py`)
1. Create `_get_keyvault_client()` using `azure.identity.DefaultAzureCredential` and `azure.keyvault.secrets.SecretClient`.
2. Implement `_fetch_credentials() -> tuple[str, str]` — retrieves `schwab-client-id` and `schwab-client-secret` from Key Vault.
3. Implement token cache dataclass with `access_token`, `expires_at`.
4. Implement `_request_token(client_id, client_secret) -> TokenCache` — POSTs to Schwab token endpoint.
5. Implement `get_access_token() -> str` — checks cache, refreshes if needed, returns bearer token.

### Step 3 — Market Data Fetching (`backend/services/schwab_market_data.py`)
1. Implement `fetch_options_chain(ticker, token)` using `httpx` with a 10 s timeout.
2. Raise `SchwabAPIError` (custom exception) on non-2xx responses.
3. Implement `fetch_all_chains(tickers)` with per-ticker error isolation (log and continue on failure).

### Step 4 — Filtering (`backend/services/schwab_filters.py`)
1. Implement `is_weekly_expiration(expiration_date)` using `dateutil.parser` — checks the date is a Friday and within 8 calendar days.
2. Implement `filter_contracts(raw_chain, delta_target=0.30, delta_tolerance=0.05)`:
   - Navigate Schwab chain response structure (`putExpDateMap`).
   - Flatten all put contracts.
   - Apply weekly and delta filters.
3. Return list of contract dicts with at minimum: `symbol`, `strikePrice`, `expirationDate`, `delta`, `bid`, `ask`, `openInterest`.

### Step 5 — Orchestrator (`backend/services/market_data_service.py`)
1. Implement `get_filtered_options(tickers)` calling the pipeline.
2. Add structured logging at each stage.

### Step 6 — Tests
Write tests as described in the test files section below.

### Step 7 — Update `backend/services/__init__.py`
Expose public interface.

---

## Test Strategy

### Unit Tests — `test_schwab_auth.py`
- Mock `SecretClient.get_secret` to return fake credentials.
- Mock `httpx.post` to return a fake token response.
- Assert token is cached and reused within TTL.
- Assert token is refreshed when within 60 s of expiry.
- Assert `KeyVaultError` propagates correctly.

### Unit Tests — `test_schwab_market_data.py`
- Mock `httpx.get` to return a fixture JSON response.
- Assert correct URL construction including ticker symbol.
- Assert `SchwabAPIError` raised on 401/500 responses.
- Assert `fetch_all_chains` continues past a single ticker failure.

### Unit Tests — `test_schwab_filters.py`
- `is_weekly_expiration`: test a known upcoming Friday, a Saturday, a Monday, and a Friday > 8 days out.
- `filter_contracts`: test with fixture chain data containing mixed put/call, mixed delta values, mixed expiration types — assert only correct contracts returned.
- Test delta boundary values (exactly 0.25, exactly 0.35, 0.24, 0.36).
- Test empty chain response returns empty list.

### Integration Tests — `test_market_data_service.py`
- Mock entire auth + HTTP stack.
- Assert `get_filtered_options(["SPY"])` returns expected filtered structure.
- Assert empty result when no contracts match filters.

---

## Edge Cases to Handle

1. **Key Vault unavailable** — `SecretClient` raises; propagate with clear error message; do not fall back to env vars.
2. **Schwab token endpoint returns 401** — raise `SchwabAuthError` with message; do not cache failed token.
3. **Ticker not found** — Schwab returns 404 or empty chain; log warning, return empty list for that ticker.
4. **No weekly expirations available** — filter returns empty list; this is valid, not an error.
5. **Delta field missing from contract** — skip contract and log warning rather than crashing.
6. **Clock skew** — use a 60-second buffer before token expiry to avoid race conditions.
7. **Rate limiting (429)** — raise `SchwabAPIError` with retry hint in message; do not implement retry logic in MVP (leave for future story).
