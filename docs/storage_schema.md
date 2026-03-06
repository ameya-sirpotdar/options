# Azure Table Storage Schema Documentation

## Overview

This document describes the Azure Table Storage schema used by the options data pipeline. The schema is implemented as Pydantic v2 models in `backend/models/` and provides serialization helpers for reading and writing entities to Azure Table Storage.

---

## Tables

### 1. `optionsdata`

Stores individual options contract data retrieved during each pipeline run.

#### Partition and Row Key Strategy

| Key          | Value       | Rationale                                                                 |
|--------------|-------------|---------------------------------------------------------------------------|
| PartitionKey | `ticker`    | Groups all options for a given underlying symbol on the same storage node |
| RowKey       | `timestamp` | Uniquely identifies a snapshot in time; ISO 8601 format (UTC)             |

Using `ticker` as the partition key allows efficient range queries across all options for a single underlying (e.g., fetch all rows for `AAPL`). The `timestamp` row key ensures records are naturally ordered chronologically within each partition.

#### Schema

| Field        | Azure Type | Python Type     | Required | Description                                              |
|--------------|------------|-----------------|----------|----------------------------------------------------------|
| PartitionKey | String     | `str`           | Yes      | Ticker symbol (e.g., `AAPL`, `SPY`)                      |
| RowKey       | String     | `str`           | Yes      | ISO 8601 UTC timestamp (e.g., `2024-01-15T10:30:00Z`)    |
| expiry       | String     | `str`           | Yes      | Option expiration date in `YYYY-MM-DD` format            |
| strike       | Double     | `float`         | Yes      | Strike price of the option contract                      |
| delta        | Double     | `float`         | Yes      | Option delta (sensitivity to underlying price change)    |
| theta        | Double     | `float`         | Yes      | Option theta (time decay per day)                        |
| iv           | Double     | `float`         | Yes      | Implied volatility as a decimal (e.g., `0.25` = 25%)     |
| premium      | Double     | `float`         | Yes      | Option premium (market price of the contract)            |

#### Example Entity

```json
{
  "PartitionKey": "AAPL",
  "RowKey": "2024-01-15T10:30:00Z",
  "expiry": "2024-02-16",
  "strike": 185.0,
  "delta": -0.35,
  "theta": -0.08,
  "iv": 0.2731,
  "premium": 3.45
}
```

#### Query Patterns

```python
# Fetch all options snapshots for a ticker
query = "PartitionKey eq 'AAPL'"

# Fetch a specific snapshot by ticker and timestamp
query = "PartitionKey eq 'AAPL' and RowKey eq '2024-01-15T10:30:00Z'"

# Fetch snapshots within a time range for a ticker
query = "PartitionKey eq 'AAPL' and RowKey ge '2024-01-01T00:00:00Z' and RowKey le '2024-01-31T23:59:59Z'"
```

---

### 2. `runlogs`

Stores metadata and status information for each pipeline execution run.

#### Partition and Row Key Strategy

| Key          | Value      | Rationale                                                                      |
|--------------|------------|--------------------------------------------------------------------------------|
| PartitionKey | `run_date` | Groups all runs by calendar date; enables efficient queries for a given day    |
| RowKey       | `run_id`   | Unique identifier (UUID) for each individual run within a date partition       |

Using `run_date` as the partition key allows operators to quickly retrieve all runs that occurred on a specific day. The UUID `run_id` row key guarantees uniqueness across concurrent or retried runs.

#### Schema

| Field        | Azure Type | Python Type     | Required | Description                                                  |
|--------------|------------|-----------------|----------|--------------------------------------------------------------|
| PartitionKey | String     | `str`           | Yes      | Calendar date of the run in `YYYY-MM-DD` format              |
| RowKey       | String     | `str`           | Yes      | UUID v4 string uniquely identifying this run                 |
| status       | String     | `str`           | Yes      | Run status: one of `pending`, `running`, `success`, `failed` |
| created_at   | String     | `str`           | Yes      | ISO 8601 UTC timestamp when the run was created              |
| message      | String     | `str`           | No       | Optional human-readable status message or error detail       |

#### Allowed Status Values

| Status    | Description                                          |
|-----------|------------------------------------------------------|
| `pending` | Run has been scheduled but not yet started           |
| `running` | Run is currently in progress                         |
| `success` | Run completed successfully                           |
| `failed`  | Run terminated with an error                         |

#### Example Entity

```json
{
  "PartitionKey": "2024-01-15",
  "RowKey": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "status": "success",
  "created_at": "2024-01-15T10:30:00Z",
  "message": "Processed 42 contracts for AAPL, SPY, QQQ"
}
```

#### Query Patterns

```python
# Fetch all runs for a specific date
query = "PartitionKey eq '2024-01-15'"

# Fetch a specific run by date and run ID
query = "PartitionKey eq '2024-01-15' and RowKey eq 'f47ac10b-58cc-4372-a567-0e02b2c3d479'"

# Fetch all failed runs for a date
query = "PartitionKey eq '2024-01-15' and status eq 'failed'"
```

---

## Key Constraints

Azure Table Storage enforces the following constraints on PartitionKey and RowKey values. The models validate these automatically via Pydantic field validators.

### Forbidden Characters

The following characters are **not allowed** in PartitionKey or RowKey values:

| Character | Unicode  | Description        |
|-----------|----------|--------------------|
| `/`       | U+002F   | Forward slash      |
| `\`       | U+005C   | Backslash          |
| `#`       | U+0023   | Hash / pound sign  |
| `?`       | U+003F   | Question mark      |

### Length Limits

| Property     | Maximum Length |
|--------------|----------------|
| PartitionKey | 1,024 characters |
| RowKey       | 1,024 characters |

### Additional Rules

- Keys must not be empty strings.
- Keys must not contain control characters in the ranges U+0000–U+001F and U+007F–U+009F.
- Leading and trailing whitespace is stripped automatically by the validators.

---

## Model Implementation

### Base Class: `AzureTableModel`

Located in `backend/models/base.py`. All table models inherit from this class.

```python
from backend.models.base import AzureTableModel
```

Provides:

- `to_entity() -> dict` — Serializes the model to a flat dictionary suitable for writing to Azure Table Storage.
- `from_entity(entity: dict) -> AzureTableModel` — Class method that deserializes an Azure Table Storage entity dictionary back into a model instance.
- Shared field validators for `PartitionKey` and `RowKey` enforcing Azure constraints.

### `OptionsData` Model

Located in `backend/models/options_data.py`.

```python
from backend.models.options_data import OptionsData

record = OptionsData(
    PartitionKey="AAPL",
    RowKey="2024-01-15T10:30:00Z",
    expiry="2024-02-16",
    strike=185.0,
    delta=-0.35,
    theta=-0.08,
    iv=0.2731,
    premium=3.45,
)

entity = record.to_entity()
restored = OptionsData.from_entity(entity)
```

### `RunLog` Model

Located in `backend/models/run_log.py`.

```python
from backend.models.run_log import RunLog

log = RunLog(
    PartitionKey="2024-01-15",
    RowKey="f47ac10b-58cc-4372-a567-0e02b2c3d479",
    status="success",
    created_at="2024-01-15T10:30:00Z",
    message="Processed 42 contracts for AAPL, SPY, QQQ",
)

entity = log.to_entity()
restored = RunLog.from_entity(entity)
```

---

## Serialization Round-Trip

Both models guarantee that `from_entity(record.to_entity()) == record`. This invariant is verified in the unit test suites under `tests/`.

```python
original = OptionsData(
    PartitionKey="SPY",
    RowKey="2024-03-01T09:00:00Z",
    expiry="2024-03-15",
    strike=510.0,
    delta=0.50,
    theta=-0.12,
    iv=0.1850,
    premium=6.20,
)

assert OptionsData.from_entity(original.to_entity()) == original
```

---

## Design Decisions

### Why Azure Table Storage?

Azure Table Storage provides a low-cost, serverless, schemaless NoSQL store well-suited for time-series and log data. It requires no infrastructure management and integrates natively with other Azure services used in this pipeline.

### Why Pydantic v2?

Pydantic v2 provides:

- Fast validation with Rust-backed core.
- Declarative field definitions with type safety.
- Built-in serialization via `model_dump()`.
- Easy extensibility for custom validators.

### Partition Key Choices

- **`optionsdata`**: Partitioning by `ticker` keeps related data co-located and supports efficient per-symbol queries. Time-range queries within a ticker are served from a single partition.
- **`runlogs`**: Partitioning by `run_date` supports operational queries like "show me all runs today" or "show me all failures this week" without full-table scans.

### Timestamp Format

All timestamps are stored as ISO 8601 strings in UTC (e.g., `2024-01-15T10:30:00Z`). This format:

- Is human-readable.
- Sorts lexicographically in the correct chronological order, which is important since RowKey ordering in Azure Table Storage is lexicographic.
- Is unambiguous with respect to time zone.

---

## Testing

Unit tests for both models are located in:

- `tests/test_models_options_data.py`
- `tests/test_models_run_log.py`

Tests cover:

- Valid entity creation.
- Field validation (type coercion, required fields).
- Key constraint validation (forbidden characters, empty strings, length limits).
- `to_entity()` output structure and types.
- `from_entity()` deserialization.
- Full serialization round-trip equality.
- Edge cases (missing optional fields, boundary values).

Run the tests with:

```bash
cd backend
pytest ../tests/ -v
```

---

## Future Considerations

- **Indexing**: Azure Table Storage does not support secondary indexes. If queries by fields other than PartitionKey/RowKey become necessary (e.g., query by `status` across all dates), consider mirroring data to Azure Cosmos DB or adding a separate index table.
- **TTL / Retention**: Azure Table Storage does not natively support TTL on individual rows. A scheduled cleanup job should be implemented to purge old `optionsdata` and `runlogs` records beyond the retention window.
- **Batch Writes**: The Azure SDK supports batch operations (up to 100 entities per batch, same partition). The pipeline should use batch inserts for `optionsdata` to reduce transaction costs.
- **Optimistic Concurrency**: Azure Table Storage supports ETags for optimistic concurrency control. The `RunLog` model may benefit from ETag-based updates when transitioning status from `running` to `success` or `failed`.