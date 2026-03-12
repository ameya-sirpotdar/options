# Implementation Plan: Cash Covered Put Annualized ROI Calculator

## Approach Overview

The annualized ROI for a Cash Covered Put is computed as:

```
annualized_roi = (bid * 365) / (strike * 100 * days_to_expiration)
```

Where `days_to_expiration = (expiration_date - current_date).days + 1`.

The implementation will:
1. Add a dedicated calculator module with the pure computation logic
2. Integrate the calculator into the existing options data agent (`options_data_agent.py`) so it enriches each put option record
3. Update the `OptionsData` model to include `annualized_roi` as an optional float field
4. Ensure the enriched data flows through the existing API router (`options_chain.py`)
5. Add comprehensive unit and integration tests

---

## Files to Create

### `backend/services/ccp_calculator.py`
Pure computation module for CCP annualized ROI. Contains:
- `compute_days_to_expiration(expiration_date: date, current_date: date | None = None) -> int`
- `compute_annualized_roi(bid: float, strike: float, days_to_expiration: int) -> float`
- `enrich_put_options_with_roi(options: list[dict], current_date: date | None = None) -> list[dict]` — iterates over put option records and appends `annualized_roi` to each

### `tests/services/test_ccp_calculator.py`
Unit tests for the calculator module covering:
- Correct formula output (example from issue: strike=600, bid=7, dte=9 → ~0.00473)
- Zero bid edge case (ROI = 0)
- DTE = 1 (minimum expiration)
- Zero strike guard (should raise ValueError or return None)
- Zero DTE guard (should raise ValueError or return None)
- Negative bid handling
- `enrich_put_options_with_roi` with a list of mock put records

---

## Files to Modify

### `backend/models/options_data.py`
- Add `annualized_roi: Optional[float] = None` field to the `OptionsData` Pydantic model (or equivalent dataclass/TypedDict)
- Add `days_to_expiration: Optional[int] = None` field if not already present

### `backend/agents/options_data_agent.py`
- Import `enrich_put_options_with_roi` from `backend.services.ccp_calculator`
- After fetching and filtering put options, call `enrich_put_options_with_roi` on the list before returning/storing results
- Ensure the enriched records are passed downstream in the agent state

### `backend/services/schwab_filters.py`
- Verify (and if needed, ensure) that `bid`, `strike`, and `expiration_date` are preserved in the filtered output — no changes expected but confirm field mapping

### `tests/agents/test_options_data_agent.py`
- Add test cases asserting that `annualized_roi` is present and correctly computed on the output records after agent execution
- Mock `enrich_put_options_with_roi` to isolate agent logic from calculator logic

### `tests/test_options_data_model.py`
- Add tests for the new `annualized_roi` and `days_to_expiration` optional fields on the model

---

## Implementation Steps

### Step 1 — Create `backend/services/ccp_calculator.py`

```python
from datetime import date
from typing import Optional


def compute_days_to_expiration(expiration_date: date, current_date: Optional[date] = None) -> int:
    """Compute days to expiration inclusive of current day."""
    if current_date is None:
        current_date = date.today()
    delta = (expiration_date - current_date).days + 1
    return max(delta, 1)  # floor at 1 to avoid division by zero


def compute_annualized_roi(
    bid: float,
    strike: float,
    days_to_expiration: int,
) -> float:
    """
    Compute annualized ROI for a Cash Covered Put.

    Formula: (bid * 365) / (strike * 100 * days_to_expiration)

    Returns 0.0 if bid <= 0 or strike <= 0.
    Raises ValueError if days_to_expiration < 1.
    """
    if days_to_expiration < 1:
        raise ValueError(f"days_to_expiration must be >= 1, got {days_to_expiration}")
    if strike <= 0:
        raise ValueError(f"strike must be > 0, got {strike}")
    if bid <= 0:
        return 0.0
    return (bid * 365) / (strike * 100 * days_to_expiration)


def enrich_put_options_with_roi(
    options: list[dict],
    current_date: Optional[date] = None,
) -> list[dict]:
    """
    Enrich a list of put option dicts with `days_to_expiration` and `annualized_roi`.

    Each dict must contain `bid`, `strike`, and `expiration_date` (date or ISO string).
    Records with missing/invalid fields will have annualized_roi=None.
    """
    enriched = []
    for opt in options:
        record = dict(opt)
        try:
            exp = opt["expiration_date"]
            if isinstance(exp, str):
                exp = date.fromisoformat(exp)
            dte = compute_days_to_expiration(exp, current_date)
            roi = compute_annualized_roi(
                bid=float(opt["bid"]),
                strike=float(opt["strike"]),
                days_to_expiration=dte,
            )
            record["days_to_expiration"] = dte
            record["annualized_roi"] = roi
        except (KeyError, TypeError, ValueError):
            record["days_to_expiration"] = record.get("days_to_expiration")
            record["annualized_roi"] = None
        enriched.append(record)
    return enriched
```

### Step 2 — Update `backend/models/options_data.py`

Add the two new optional fields to the model:

```python
days_to_expiration: Optional[int] = None
annualized_roi: Optional[float] = None
```

### Step 3 — Integrate into `backend/agents/options_data_agent.py`

After the agent retrieves and filters put options, call:

```python
from backend.services.ccp_calculator import enrich_put_options_with_roi

# ... existing fetch/filter logic ...
enriched_puts = enrich_put_options_with_roi(filtered_puts)
# pass enriched_puts downstream
```

### Step 4 — Write Tests

Create `tests/services/test_ccp_calculator.py` with full coverage of the calculator.
Update `tests/agents/test_options_data_agent.py` to assert ROI enrichment.
Update `tests/test_options_data_model.py` for new fields.

### Step 5 — Verify API Output

Confirm that `backend/api/routers/options_chain.py` serializes the model fields correctly — since `annualized_roi` is added to the model, it should appear in JSON responses automatically via Pydantic serialization. No router changes expected unless the response schema explicitly excludes unknown fields.

---

## Test Strategy

### Unit Tests (`tests/services/test_ccp_calculator.py`)
- **Happy path**: strike=600, bid=7, dte=9 → annualized_roi ≈ 0.004731
- **Zero bid**: returns 0.0
- **Negative bid**: returns 0.0
- **DTE=1**: formula works at minimum expiration
- **Zero strike**: raises ValueError
- **DTE=0**: raises ValueError (or is floored to 1 depending on design choice)
- **enrich_put_options_with_roi**: list of 3 records, one with missing field → that record gets `annualized_roi=None`, others computed correctly
- **String expiration_date**: ISO string parsed correctly

### Integration Tests (`tests/agents/test_options_data_agent.py`)
- Mock Schwab API response with put options containing bid/strike/expiration_date
- Assert agent output contains `annualized_roi` field on each record
- Assert values are numerically correct

### Model Tests (`tests/test_options_data_model.py`)
- `annualized_roi` defaults to None
- `days_to_expiration` defaults to None
- Both fields accept float/int values
- Serialization includes both fields in JSON output

---

## Edge Cases to Handle

1. **Zero or negative DTE** — can happen if expiration is in the past; floor at 1 or skip record
2. **Zero bid** — valid scenario (deep OTM); return 0.0 ROI
3. **Zero or negative strike** — invalid data; raise ValueError or return None
4. **Missing fields** — `enrich_put_options_with_roi` should not crash; set `annualized_roi=None`
5. **Expiration date as string vs date object** — handle both ISO string and `date` type
6. **Very large ROI values** — no cap needed, but display layer may want to format as percentage
