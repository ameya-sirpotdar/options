# Epic 5: Tradability Index Engine

**Copy the content below into a new GitHub issue (title + body).**

---

## Title

```
Epic 5: Tradability Index Engine (5.1 Metric Extraction, 5.2 Formula, 5.3 Ranking)
```

---

## Body

### Goal

Implement the Tradability Index engine: extract metrics from options data, compute the tradability score with the agreed formula, and rank candidate trades to return the best one.

**Reference:** [docs/options_agent_mvp_epics.md — EPIC 5](docs/options_agent_mvp_epics.md)

---

### Story 5.1 – Metric Extraction

- [ ] Extract from stored options data (per contract):
  - `delta`
  - `theta`
  - `iv` (implied volatility)
  - `premium`
- [ ] Expose these fields for use by the tradability formula (e.g. in `services/` or `models/`).

---

### Story 5.2 – Tradability Formula

- [ ] Implement the tradability score formula:

  ```
  score = (theta_weight * theta)
        + (iv_weight * iv)
        + (premium_weight * premium)
        - (delta_risk_weight * abs(delta - 0.30))
  ```

- [ ] Make weights configurable (e.g. env or config).
- [ ] Unit tests for the formula with known inputs/outputs.

---

### Story 5.3 – Ranking

- [ ] Compute tradability score for all candidate contracts (using 5.1 + 5.2).
- [ ] Rank candidates by score (e.g. descending).
- [ ] Return the best trade (e.g. single top candidate or top N).
- [ ] Integrate with `GET /trades/best` (or equivalent) so the API can return the best trade.

---

### Acceptance criteria (Epic-level)

- Metrics (delta, theta, iv, premium) are extracted from options data.
- Tradability score is computed per contract using the formula above.
- Candidates are ranked and the best trade is deterministically selected.
- Best trade is available to the API layer for `GET /trades/best`.

---

### Notes

- Storage schema: `optionsdata` table (PartitionKey = Ticker, RowKey = Timestamp); columns include `expiry`, `strike`, `delta`, `theta`, `iv`, `premium` (see [CLAUDE.md](CLAUDE.md) / epic 1.4).
- Prefer logic in `backend/services/` (e.g. `tradability_engine` or similar); keep API thin.
