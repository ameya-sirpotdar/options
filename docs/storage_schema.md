# Azure Table Storage Schema Design

## Overview

This document describes the Azure Table Storage schema used by the options data pipeline. The storage layer uses two tables: `optionsdata` and `runlogs`. Both tables are implemented as Pydantic v2 models with serialization helpers for Azure Table Storage entity format.

---

## Tables

### 1. `optionsdata`

Stores options chain snapshots for a given ticker at a specific point in time.

#### Partition and Row Key Strategy

| Key          | Maps To     | Format                          | Example                        |
|--------------|-------------|----------------------------------|--------------------------------|
| PartitionKey | `ticker`    | Uppercase alphabetic string      | `AAPL`                         |
| RowKey       | `timestamp` | ISO 8601 UTC datetime string     | `2024-01-15T09:30:00Z`         |

**Rationale:**
- Partitioning by ticker groups all snapshots for a given underlying together, enabling efficient range queries over time for a single ticker.
- Using the ISO 8601 timestamp as the RowKey provides natural chronological ordering within each partition and guarantees uniqueness when snapshots are taken at distinct moments.

#### Fields

| Field            | Type     | Required | Constraints                                                                 |
|------------------|----------|----------|-----------------------------------------------------------------------------|
| `ticker`         | `str`    | Yes      | 1–10 characters, uppercase letters only, no Azure reserved characters       |
| `timestamp`      | `str`    | Yes      | ISO 8601 UTC format (`YYYY-MM-DDTHH:MM:SSZ`)                               |
| `expiration`     | `str`    | Yes      | Date string in `YYYY-MM-DD` format                                          |
| `strike`         | `float`  | Yes      | Must be greater than 0                                                      |
| `option_type`    | `str`    | Yes      | One of `"call"` or `"put"` (case-insensitive, stored lowercase)             |
| `bid`            | `float`  | Yes      | Must be >= 0                                                                |
| `ask`            | `float`  | Yes      | Must be >= 0                                                                |
| `volume`         | `int`    | Yes      | Must be >= 0                                                                |
| `open_interest`  | `int`    | Yes      | Must be >= 0                                                                |
| `implied_volatility` | `float` | Yes  | Must be >= 0                                                                |
| `delta`          | `float`  | No       | Range: -1.0 to 1.0                                                          |
| `gamma`          | `float`  | No       | Must be >= 0                                                                |
| `theta`          | `float`  | No       | No range constraint (typically negative)                                    |
| `vega`           | `float`  | No       | Must be >= 0                                                                |

#### Azure Table Entity Example

```json
{
  "PartitionKey": "AAPL",
  "RowKey": "2024-01-15T09:30:00Z",
  "expiration": "2024-02-16",
  "strike": 185.0,
  "option_type": "call",
  "bid": 3.20,
  "ask": 3.35,
  "volume": 1042,
  "open_interest": 8765,
  "implied_volatility": 0.2731,
  "delta": 0.52,
  "gamma": 0.08,
  "theta": -0.045,
  "vega": 0.19
}
```

---

### 2. `runlogs`

Stores execution records for pipeline runs, enabling auditing, monitoring, and failure recovery.

#### Partition and Row Key Strategy

| Key          | Maps To    | Format                     | Example          |
|--------------|------------|----------------------------|------------------|
| PartitionKey | `run_date` | `YYYY-MM-DD` date string   | `2024-01-15`     |
| RowKey       | `run_id`   | UUID v4 string             | `3f2a1b4c-...`   |

**Rationale:**
- Partitioning by date groups all runs that occurred on the same calendar day, which aligns naturally with operational queries such as "show me all runs from yesterday."
- Using a UUID as the RowKey guarantees global uniqueness without coordination and avoids hotspot issues that sequential integers could introduce.

#### Fields

| Field       | Type           | Required | Constraints                                                       |
|-------------|----------------|----------|-------------------------------------------------------------------|
| `run_date`  | `str`          | Yes      | `YYYY-MM-DD` format                                               |
| `run_id`    | `str`          | Yes      | Valid UUID v4 string                                              |
| `status`    | `RunStatus`    | Yes      | Enum: `"pending"`, `"running"`, `"success"`, `"failure"`          |
| `message`   | `str`          | No       | Optional free-text message, max 32,000 characters                 |
| `started_at`| `str`          | No       | ISO 8601 UTC datetime string                                      |
| `ended_at`  | `str`          | No       | ISO 8601 UTC datetime string                                      |
| `ticker`    | `str`          | No       | Uppercase alphabetic string, 1–10 characters                      |
| `records_processed` | `int` | No       | Must be >= 0                                                      |

#### `RunStatus` Enum

| Value       | Meaning                                              |
|-------------|------------------------------------------------------|
| `pending`   | Run has been created but not yet started             |
| `running`   | Run is currently in progress                         |
| `success`   | Run completed successfully                           |
| `failure`   | Run encountered an error and did not complete        |

#### Azure Table Entity Example

```json
{
  "PartitionKey": "2024-01-15",
  "RowKey": "3f2a1b4c-d5e6-7890-abcd-ef1234567890",
  "status": "success",
  "message": "Processed 142 option contracts for AAPL.",
  "started_at": "2024-01-15T09:28:00Z",
  "ended_at": "2024-01-15T09:30:05Z",
  "ticker": "AAPL",
  "records_processed": 142
}
```

---

## Base Model

Both `OptionsData` and `RunLog` inherit from `AzureTableModel`, a shared base class that provides:

### `to_entity() -> dict`

Serializes the model to a flat dictionary suitable for writing to Azure Table Storage. The output always includes `PartitionKey` and `RowKey` derived from the model's logical fields. Fields with `None` values are excluded from the output to avoid storing null properties unnecessarily.

### `from_entity(entity: dict) -> Self`

Class method that deserializes an Azure Table Storage entity dictionary back into a model instance. Maps `PartitionKey` and `RowKey` back to their logical field names before constructing the model, so all validation rules are re-applied on read.

---

## Azure Table Storage Constraints

The following Azure Table Storage constraints are enforced at the model level:

### Forbidden Characters in Keys

The characters listed below are not permitted in `PartitionKey` or `RowKey` values. Validators on `ticker`, `timestamp`, `run_date`, and `run_id` reject any value containing these characters:

| Character | Unicode  | Description              |
|-----------|----------|--------------------------|
| `/`       | U+002F   | Forward slash            |
| `\`       | U+005C   | Backslash                |
| `#`       | U+0023   | Hash / pound sign        |
| `?`       | U+003F   | Question mark            |
| Control characters | U+0000–U+001F, U+007F–U+009F | Non-printable control characters |

### Key Length Limits

| Limit        | Value         |
|--------------|---------------|
| Maximum key size | 1,024 bytes (UTF-16 encoded) |
| Maximum entity size | 1 MB      |
| Maximum string property size | 64 KB (32,000 characters) |

### Property Type Mapping

| Python Type | Azure Table Type |
|-------------|-----------------|
| `str`       | `Edm.String`    |
| `int`       | `Edm.Int32` / `Edm.Int64` |
| `float`     | `Edm.Double`    |
| `bool`      | `Edm.Boolean`   |

---

## Query Patterns

### `optionsdata` Table

| Query                                      | Key Usage                                                  |
|--------------------------------------------|------------------------------------------------------------|
| All snapshots for a ticker                 | `PartitionKey eq 'AAPL'`                                   |
| Snapshots for a ticker in a time range     | `PartitionKey eq 'AAPL' and RowKey ge '2024-01-01T00:00:00Z' and RowKey lt '2024-02-01T00:00:00Z'` |
| Single snapshot for a ticker at a time     | `PartitionKey eq 'AAPL' and RowKey eq '2024-01-15T09:30:00Z'` |

### `runlogs` Table

| Query                                      | Key Usage                                                  |
|--------------------------------------------|------------------------------------------------------------|
| All runs on a given date                   | `PartitionKey eq '2024-01-15'`                             |
| A specific run by ID                       | `PartitionKey eq '2024-01-15' and RowKey eq '<uuid>'`      |
| All failed runs on a date                  | `PartitionKey eq '2024-01-15' and status eq 'failure'`     |

> **Note:** Queries that filter on non-key properties (such as `status`) result in a partition scan rather than a point or range lookup. For high-volume tables, consider maintaining a secondary index or using Azure Table Storage's filter capabilities with awareness of the associated read cost.

---

## Design Decisions and Trade-offs

### Why not use a timestamp as the `runlogs` RowKey?

A timestamp RowKey would work but creates a risk of collision if two runs start within the same second. A UUID eliminates this risk entirely without requiring a distributed counter or coordination service.

### Why store `run_date` separately from `started_at`?

`run_date` is the partition key and must be a simple, stable string. `started_at` is an optional precise timestamp recorded when the run actually begins. Keeping them separate avoids coupling the partitioning strategy to the precision of the start time and allows a run record to be created (with status `pending`) before it has actually started.

### Why exclude `None` fields from `to_entity()`?

Azure Table Storage charges for stored data and has a per-entity property limit of 255 properties. Omitting null fields keeps entities lean and avoids consuming property slots for data that is not present. The `from_entity()` method handles missing properties gracefully by treating them as `None` for optional fields.

### Why enforce uppercase-only tickers?

Ticker symbols on major exchanges are conventionally uppercase. Enforcing this at the model layer prevents case-sensitivity bugs in partition key lookups, where `"aapl"` and `"AAPL"` would be treated as different partitions.

---

## File Locations

| File                              | Purpose                                      |
|-----------------------------------|----------------------------------------------|
| `backend/models/base.py`          | `AzureTableModel` base class                 |
| `backend/models/options_data.py`  | `OptionsData` model                          |
| `backend/models/run_log.py`       | `RunLog` model and `RunStatus` enum          |
| `backend/models/__init__.py`      | Package exports                              |
| `tests/test_models_options_data.py` | Unit tests for `OptionsData`               |
| `tests/test_models_run_log.py`    | Unit tests for `RunLog`                      |
| `docs/storage_schema.md`          | This document                                |