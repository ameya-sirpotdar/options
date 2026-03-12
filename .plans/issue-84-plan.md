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

## Commit & Push Plan

Each commit is self-contained, passes CI, and represents a single logical change. Commits are ordered so that later commits always build on a green baseline.

---

### Commit 1 — `feat: add ccp_calculator service module`

**Branch:** `feature/ccp-roi-calculator`

**What changes:**
- Create `backend/services/ccp_calculator.py` with the three pure functions:
  - `compute_days_to_expiration`
  - `compute_annualized_roi`
  - `enrich_put_options_with_roi`

**Why isolated:** The calculator has zero dependencies on the rest of the codebase. Landing it first means every subsequent commit can import from it without introducing a circular dependency or a broken import.

**Files:**
```
backend/services/ccp_calculator.py   ← new
```

**Code:**
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

    Returns 0.0 if bid <= 0.
    Raises ValueError if strike <= 0 or days_to_expiration < 1.
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

**CI must pass:** import check, linting (ruff/flake8), type check (mypy).

---

### Commit 2 — `test: add unit tests for ccp_calculator`

**What changes:**
- Create `tests/services/test_ccp_calculator.py` with full coverage of the calculator module

**Why isolated:** Tests for the calculator are committed immediately after the module so the test suite is green before any integration work begins. Reviewers can verify correctness of the formula independently of the agent or model changes.

**Files:**
```
tests/services/test_ccp_calculator.py   ← new
```

**Test cases covered:**

| Test | Scenario | Expected |
|---|---|---|
| `test_happy_path` | strike=600, bid=7, dte=9 | ≈ 0.004731 |
| `test_zero_bid` | bid=0 | 0.0 |
| `test_negative_bid` | bid=-1 | 0.0 |
| `test_dte_one` | dte=1 | formula result |
| `test_zero_strike_raises` | strike=0 | `ValueError` |
| `test_negative_strike_raises` | strike=-50 | `ValueError` |
| `test_zero_dte_raises` | dte=0 | `ValueError` |
| `test_enrich_happy_path` | 2 valid records | both have `annualized_roi` |
| `test_enrich_missing_field` | 1 record missing `bid` | `annualized_roi=None` |
| `test_enrich_string_expiration` | ISO string date | parsed and computed correctly |
| `test_enrich_past_expiration` | expiration yesterday | `days_to_expiration=1` (floored) |

**CI must pass:** all new tests green, coverage does not drop.

---

### Commit 3 — `feat: add annualized_roi and days_to_expiration to OptionsData model`

**What changes:**
- Add two optional fields to `backend/models/options_data.py`

**Why isolated:** The model change is a pure, non-breaking addition. Landing it before the agent integration means the agent commit can reference the updated model without a forward dependency.

**Files:**
```
backend/models/options_data.py   ← modified
```

**Diff (additions only):**
```python
days_to_expiration: Optional[int] = None
annualized_roi: Optional[float] = None
```

**CI must pass:** existing model tests still green, Pydantic schema generation succeeds.

---

### Commit 4 — `test: add model tests for annualized_roi and days_to_expiration fields`

**What changes:**
- Update `tests/test_options_data_model.py` with tests for the two new fields

**Why isolated:** Model tests are committed right after the model change, keeping the test-to-code ratio balanced and making it easy to bisect if a model regression appears later.

**Files:**
```
tests/test_options_data_model.py   ← modified
```

**Test cases added:**

| Test | Assertion |
|---|---|
| `test_annualized_roi_defaults_none` | field defaults to `None` |
| `test_days_to_expiration_defaults_none` | field defaults to `None` |
| `test_annualized_roi_accepts_float` | accepts `0.004731` |
| `test_days_to_expiration_accepts_int` | accepts `9` |
| `test_serialization_includes_new_fields` | both keys present in `.model_dump()` / `.dict()` |

**CI must pass:** all tests green.

---

### Commit 5 — `feat: enrich put options with ROI in options_data_agent`

**What changes:**
- Import `enrich_put_options_with_roi` in `backend/agents/options_data_agent.py`
- Call it on the filtered put options list before passing records downstream
- Verify `backend/services/schwab_filters.py` preserves `bid`, `strike`, and `expiration_date` (comment added if confirmed, no code change expected)

**Why isolated:** Agent integration is the only commit that wires the calculator into live data flow. Keeping it separate from the model and calculator commits means a revert here does not touch the model or the pure logic.

**Files:**
```
backend/agents/options_data_agent.py     ← modified
backend/services/schwab_filters.py      ← reviewed, comment added if needed
```

**Key change in agent:**
```python
from backend.services.ccp_calculator import enrich_put_options_with_roi

# ... existing fetch/filter logic ...
enriched_puts = enrich_put_options_with_roi(filtered_puts)
# pass enriched_puts downstream instead of filtered_puts
```

**CI must pass:** existing agent tests still green.

---

### Commit 6 — `test: add agent integration tests for ROI enrichment`

**What changes:**
- Update `tests/agents/test_options_data_agent.py` with tests asserting ROI enrichment on agent output

**Why isolated:** Integration tests are committed after the agent change so the diff is reviewable on its own. Mocking `enrich_put_options_with_roi` in some tests and using the real function in others keeps unit and integration concerns explicit.

**Files:**
```
tests/agents/test_options_data_agent.py   ← modified
```

**Test cases added:**

| Test | Strategy | Assertion |
|---|---|---|
| `test_agent_calls_enrich` | mock `enrich_put_options_with_roi` | mock called once with filtered puts |
| `test_agent_output_has_annualized_roi` | real calculator, mocked Schwab API | `annualized_roi` present on each output record |
| `test_agent_output_roi_value_correct` | real calculator, mocked Schwab API | value matches formula for known inputs |

**CI must pass:** all tests green, no regressions.

---

### Commit 7 — `chore: verify API serialization of annualized_roi`

**What changes:**
- Review `backend/api/routers/options_chain.py` to confirm `annualized_roi` appears in JSON responses
- If the response model explicitly excludes fields, update the response schema to include the new fields
- Add a brief comment in the router referencing the new fields for future maintainers
- No functional code change expected; if a schema update is required it is made here

**Why isolated:** Keeping the API verification as its own commit makes it easy to see whether any router change was needed and provides a clear audit trail.

**Files:**
```
backend/api/routers/options_chain.py   ← reviewed, modified only if schema exclusion found
```

**CI must pass:** all tests green, API schema generation succeeds.

---

## Push Strategy

```
Commit 1  →  push  →  open PR draft
Commit 2  →  push  →  CI confirms calculator tests green
Commit 3  →  push  →  CI confirms model change non-breaking
Commit 4  →  push  →  CI confirms model tests green
Commit 5  →  push  →  CI confirms agent wiring green
Commit 6  →  push  →  CI confirms integration tests green
Commit 7  →  push  →  mark PR ready for review
```

Each push triggers CI. If any push fails, only the delta since the last green push needs investigation. The PR is marked ready only after all seven commits are green end-to-end.

---

## Files Summary

| File | Action | Commit |
|---|---|---|
| `backend/services/ccp_calculator.py` | Create | 1 |
| `tests/services/test_ccp_calculator.py` | Create | 2 |
| `backend/models/options_data.py` | Modify | 3 |
| `tests/test_options_data_model.py` | Modify | 4 |
| `backend/agents/options_data_agent.py` | Modify | 5 |
| `backend/services/schwab_filters.py` | Review / minor comment | 5 |
| `tests/agents/test_options_data_agent.py` | Modify | 6 |
| `backend/api/routers/options_chain.py` | Review / modify if needed | 7 |