# Implementation Plan: Storage Schema Design (Issue #7)

## Approach

Create Pydantic v2 models that map directly to Azure Table Storage entities for the `optionsdata` and `runlogs` tables. Each model will include:
- Field definitions matching the schema
- Validators for key fields (e.g. timestamp format, ticker format)
- Methods to serialize to Azure Table entity dicts and deserialize from them
- A schema documentation file

## Files to Create

### `backend/models/options_data.py`
Pydantic model for the `optionsdata` table:
- `PartitionKey` → `ticker` (e.g. `NVDA`)
- `RowKey` → `timestamp` (ISO 8601, e.g. `2026-03-05T06:31`)
- Fields: `expiry` (date string), `strike` (float), `delta` (float), `theta` (float), `iv` (float), `premium` (float)
- `to_entity()` → dict suitable for Azure Table Storage SDK
- `from_entity(entity: dict)` → classmethod to deserialize

### `backend/models/run_log.py`
Pydantic model for the `runlogs` table:
- `PartitionKey` → `run_date` (e.g. `2026-03-05`)
- `RowKey` → `run_id` (UUID or sequential string)
- Additional fields TBD but at minimum: `status`, `created_at`, `message` (optional)
- `to_entity()` and `from_entity()` methods

### `backend/models/base.py`
Shared base class/mixin for Azure Table Storage entity serialization:
- `AzureTableModel` base class with common `to_entity()` / `from_entity()` logic
- Handles mapping between Pydantic field names and Azure Table property names

### `docs/storage_schema.md`
Schema documentation covering:
- Table names and purpose
- PartitionKey / RowKey design rationale
- All columns with types and descriptions
- Example entity payloads
- Notes on Azure Table Storage constraints (string keys, supported types)

### `tests/test_models_options_data.py`
Unit tests for `OptionsData` model.

### `tests/test_models_run_log.py`
Unit tests for `RunLog` model.

## Files to Modify

### `backend/models/__init__.py`
Export `OptionsData` and `RunLog` models so they are importable from `backend.models`.

### `backend/requirements.txt`
Ensure `pydantic>=2.0` and `azure-data-tables` are listed as dependencies.

## Implementation Steps

1. **Create `backend/models/base.py`** — define `AzureTableModel` base class with `to_entity()` and `from_entity()` helpers. Use Pydantic `model_config` to allow population by field name and alias.

2. **Create `backend/models/options_data.py`** — define `OptionsData(AzureTableModel)` with all required fields. Add field validators:
   - `ticker`: uppercase string, 1–5 chars
   - `timestamp`: must parse as ISO 8601 datetime (minute precision)
   - `expiry`: must parse as a valid date string
   - `strike`, `delta`, `theta`, `iv`, `premium`: floats with reasonable range checks (e.g. `iv >= 0`, `premium >= 0`)

3. **Create `backend/models/run_log.py`** — define `RunLog(AzureTableModel)` with `run_date`, `run_id`, `status` (enum: `pending`, `running`, `success`, `failed`), `created_at`, and optional `message`.

4. **Update `backend/models/__init__.py`** — add imports for `OptionsData` and `RunLog`.

5. **Update `backend/requirements.txt`** — add `pydantic>=2.0,<3.0` and `azure-data-tables>=12.0.0` if not already present.

6. **Create `docs/storage_schema.md`** — write full schema documentation with example payloads.

7. **Write tests** — cover serialization round-trips, validation errors, and edge cases.

## Test Strategy

- **Unit tests** for each model:
  - Valid construction with all fields
  - `to_entity()` produces correct dict with `PartitionKey`/`RowKey`
  - `from_entity()` round-trips correctly (entity → model → entity)
  - Validation rejects invalid tickers, bad timestamps, negative premiums, etc.
- **Type coercion tests**: Azure Table Storage returns some numeric types as `Decimal` or `str`; ensure `from_entity()` handles these.
- **Edge cases**: empty optional fields, maximum float values, special characters in `run_id`.

## Edge Cases to Handle

- Azure Table Storage keys cannot contain `/`, `\`, `#`, `?` — validate ticker and run_id accordingly
- Timestamps stored as strings (Azure Table Storage `Edm.String`) vs `Edm.DateTime` — document chosen approach
- Float precision: Azure Table Storage uses `Edm.Double`; ensure no silent truncation
- `expiry` field: store as `YYYY-MM-DD` string for portability
- `run_id` uniqueness: document that callers are responsible for providing unique IDs (UUID recommended)
