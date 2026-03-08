# Implementation Plan: Azure Table Storage Persistence (Issue #21)

## Approach Overview

We will introduce a dedicated Azure Table Storage service that handles writes to two tables:
- `optionsdata` — one entity per options contract per polling run
- `runlogs` — one entity per polling run

The existing `polling_service.py` will be updated to call the persistence layer after each successful Schwab API fetch. Pydantic models in `backend/models/` will be expanded to cover all required fields. Missing fields from the API response will be coerced to `None` / empty values rather than raising errors.

---

## Files to Create

### `backend/models/options_data.py`
Pydantic model (`OptionsContractRecord`) covering all fields listed in the issue:
- Greeks & pricing fields
- Contract metadata fields
- Boolean flags
- Underlying snapshot fields
- Partition/row key helpers for Azure Table Storage (`runId` as PartitionKey, OCC `symbol` as RowKey)

### `backend/models/run_log.py`
Pydantic model (`RunLogRecord`) with:
- `runId` (UUID, PartitionKey)
- `timestamp` (ISO 8601)
- `tickersProcessed` (list → comma-separated string for ATS)
- `recordsStored` (int)
- `status` (str: `success` / `partial` / `error`)
- `errorDetail` (optional str)

### `backend/services/azure_table_service.py`
Service class `AzureTableService` wrapping `azure-data-tables` SDK:
- `__init__`: reads `AZURE_STORAGE_CONNECTION_STRING` (or account name + key) from env; lazily creates table clients for `optionsdata` and `runlogs`
- `upsert_options_records(records: list[OptionsContractRecord]) -> int`: batch upsert (merge) to `optionsdata`; returns count of records written
- `write_run_log(log: RunLogRecord) -> None`: single entity upsert to `runlogs`
- `_ensure_tables()`: creates tables if they do not exist (idempotent)
- All methods catch `azure.core.exceptions.AzureError` and re-raise as a typed `PersistenceError`

### `backend/models/__init__.py` (update, not new)
Re-export new models.

### `tests/test_azure_table_service.py`
Unit tests using `unittest.mock` to mock `azure-data-tables` client.

### `tests/test_options_data_model.py`
Unit tests for model field coercion and serialisation.

### `tests/test_run_log_model.py`
Unit tests for `RunLogRecord` serialisation.

---

## Files to Modify

### `backend/models/poll.py`
- If it contains any partial options/run-log model definitions, reconcile or remove them in favour of the new dedicated model files.

### `backend/services/polling_service.py`
- Import `AzureTableService`, `OptionsContractRecord`, `RunLogRecord`.
- After a successful Schwab fetch, map raw contract dicts → `OptionsContractRecord` list.
- Call `azure_table_service.upsert_options_records(records)`.
- After processing all tickers, call `azure_table_service.write_run_log(run_log)`.
- Wrap persistence calls in try/except so a storage failure logs a warning but does not crash the poll cycle.
- Pass `runId` (UUID generated at poll-start) through the flow.

### `backend/agents/options_agent.py`
- If the agent is responsible for invoking the polling service, ensure `runId` is threaded through correctly.

### `backend/requirements.txt`
- Add `azure-data-tables>=12.5.0`

### `backend/main.py`
- Instantiate `AzureTableService` once at startup (singleton / dependency injection) and pass to `polling_service`.

---

## Implementation Steps

1. **Add dependency** — append `azure-data-tables>=12.5.0` to `backend/requirements.txt`.
   - Commit: `chore: add azure-data-tables dependency to requirements.txt`
   - Push to feature branch: `git push origin feature/issue-21-azure-table-persistence`

2. **Create `backend/models/options_data.py`**
   - Define `OptionsContractRecord(BaseModel)` with all ~45 fields, all optional with `None` defaults.
   - Add `partition_key` property returning `runId`.
   - Add `row_key` property returning `symbol` (OCC).
   - Add `to_entity()` method that converts the model to a flat dict suitable for Azure Table Storage (no nested objects; booleans as bool, floats as float, None fields omitted or stored as empty string per ATS constraints).
   - Commit: `feat: add OptionsContractRecord pydantic model`
   - Push: `git push origin feature/issue-21-azure-table-persistence`

3. **Create `backend/models/run_log.py`**
   - Define `RunLogRecord(BaseModel)` with fields listed above.
   - Add `to_entity()` method; convert `tickersProcessed` list to comma-separated string.
   - Commit: `feat: add RunLogRecord pydantic model`
   - Push: `git push origin feature/issue-21-azure-table-persistence`

4. **Update `backend/models/__init__.py`**
   - Re-export `OptionsContractRecord` and `RunLogRecord`.
   - Commit: `chore: re-export new models from backend/models/__init__.py`
   - Push: `git push origin feature/issue-21-azure-table-persistence`

5. **Create `backend/services/azure_table_service.py`**
   - Implement `AzureTableService` as described.
   - Use `TableClient.upsert_entity(mode=UpdateMode.MERGE)` for options records.
   - Batch writes using `TableClient.submit_transaction` in chunks of 100 (ATS batch limit) within the same PartitionKey.
   - Expose `upsert_options_records` and `write_run_log`.
   - Commit: `feat: implement AzureTableService with batch upsert and run log write`
   - Push: `git push origin feature/issue-21-azure-table-persistence`

6. **Update `backend/services/polling_service.py`**
   - Generate `runId = str(uuid.uuid4())` at the start of each poll cycle.
   - After fetching and filtering contracts for each ticker, map to `OptionsContractRecord` objects (use `.get()` with `None` default for every field).
   - Accumulate all records across tickers.
   - Call `azure_table_service.upsert_options_records(all_records)`.
   - Build and write `RunLogRecord`.
   - Commit: `feat: integrate AzureTableService into polling_service`
   - Push: `git push origin feature/issue-21-azure-table-persistence`

7. **Update `backend/agents/options_agent.py`**
   - Thread `runId` through correctly if the agent invokes the polling service.
   - Commit: `fix: thread runId through options_agent to polling_service`
   - Push: `git push origin feature/issue-21-azure-table-persistence`

8. **Update `backend/main.py`**
   - Wire `AzureTableService` instantiation at startup and inject into `polling_service`.
   - Commit: `feat: instantiate AzureTableService at startup in main.py`
   - Push: `git push origin feature/issue-21-azure-table-persistence`

9. **Document environment variables**
   - Add required variables to `infra/README.md` or a new `backend/.env.example`.
   - Commit: `docs: document Azure Storage environment variables in .env.example`
   - Push: `git push origin feature/issue-21-azure-table-persistence`

10. **Write tests**
    - Add `tests/test_options_data_model.py`, `tests/test_run_log_model.py`, `tests/test_azure_table_service.py`, and extend `tests/test_poll_options.py`.
    - Commit: `test: add unit and integration tests for Azure Table Storage persistence`
    - Push: `git push origin feature/issue-21-azure-table-persistence`

11. **Open pull request**
    - Open a PR from `feature/issue-21-azure-table-persistence` → `main` referencing Issue #21.
    - Ensure CI passes before requesting review.

---

## Field Mapping Reference

```python
# Greeks & pricing
delta, gamma, theta, vega, rho
bid, ask, last, mark
openPrice, closePrice, highPrice, lowPrice
netChange, markChange, markPercentChange, percentChange
volatility, theoreticalOptionValue, theoreticalVolatility
intrinsicValue, timeValue

# Contract metadata
symbol, description, putCall, strikePrice
expirationDate, expirationType, daysToExpiration
lastTradingDay, multiplier, settlementType
openInterest, totalVolume
bidSize, askSize, lastSize
tradeTimeInLong, quoteTimeInLong

# Flags
inTheMoney, nonStandard, mini, pennyPilot

# Underlying snapshot
underlyingPrice, underlyingSymbol, interestRate, isDelayed, isIndex

# Persistence metadata (added by us)
runId, fetchedAt (UTC ISO timestamp)
```

---

## Test Strategy

### Unit Tests
- `test_options_data_model.py`:
  - All fields present → serialises correctly
  - Missing fields → default to `None`, no validation error
  - `to_entity()` produces flat dict with correct types
  - `partition_key` / `row_key` return expected values
- `test_run_log_model.py`:
  - `to_entity()` converts ticker list to comma-separated string
  - Required fields enforced
- `test_azure_table_service.py`:
  - `upsert_options_records` calls `submit_transaction` in correct batch sizes
  - `write_run_log` calls `upsert_entity` once
  - `AzureError` is caught and re-raised as `PersistenceError`
  - `_ensure_tables` is called on init

### Integration Tests (mocked ATS)
- `test_poll_options.py` (extend existing):
  - Full poll cycle with mocked Schwab API + mocked ATS → verify `upsert_options_records` called with correct record count
  - Verify `write_run_log` called once per poll with correct `tickersProcessed`
  - Verify poll does not raise if ATS throws `AzureError`

### Edge Cases
- Empty options chain response (no contracts) → `runlogs` entry written with `recordsStored=0`
- Partial ticker failure (one ticker errors) → remaining tickers still persisted; run log reflects partial status
- ATS batch boundary: >100 contracts → multiple transactions submitted
- Duplicate `runId` + `symbol` → upsert (merge) overwrites cleanly
- `None` float fields → stored as empty string or omitted (ATS does not support null natively)

---

## Branch and Commit Strategy

All work is done on a single feature branch created from `main` before any changes begin:

```bash
git checkout main
git pull origin main
git checkout -b feature/issue-21-azure-table-persistence
```

Each implementation step above has its own atomic commit with a conventional commit message. After every commit, push immediately so work is visible on the remote and CI runs incrementally:

```bash
git push origin feature/issue-21-azure-table-persistence
```

Once all steps are complete and CI is green, open a pull request from `feature/issue-21-azure-table-persistence` → `main` referencing `Closes #21` in the PR description.

---

## Environment Variables Required

```
AZURE_STORAGE_CONNECTION_STRING   # preferred
# OR
AZURE_STORAGE_ACCOUNT_NAME
AZURE_STORAGE_ACCOUNT_KEY
```

Document in `infra/README.md` or a new `backend/.env.example`.