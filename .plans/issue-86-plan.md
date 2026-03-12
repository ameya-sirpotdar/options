# Implementation Plan: Display CCP Annualized ROI Column in Options Chain Table

## Approach

The backend already provides `annualizedRoi` (and `daysToExpiration`) on put option records. The work is entirely frontend:

1. Add an **Annualized ROI** column to `OptionsTable.vue` that displays `annualizedRoi` formatted as a percentage (e.g. `12.34%`) for put options.
2. Handle cases where the value is `null`, `undefined`, or not present (e.g. for call options or when the API doesn't return the field) — display `—` or `N/A`.
3. Update the existing unit tests in `OptionsTable.spec.js` to assert the new column renders correctly.
4. Optionally update the e2e test to verify the column appears in the rendered table.

---

## Files to Modify

### `frontend/vue-app/src/components/OptionsTable.vue`
- Add a new `<th>` header cell: **Annualized ROI**
- Add a corresponding `<td>` data cell in each row that:
  - Reads `option.annualizedRoi`
  - Formats it as a percentage string (e.g. `(annualizedRoi * 100).toFixed(2) + '%'`) — or if the value is already a percentage number, just `.toFixed(2) + '%'`
  - Falls back to `'—'` when the value is absent/null
- Consider placing the column near other financial metrics (e.g. after premium/bid/ask columns)
- Optionally apply a CSS class for positive ROI values to aid readability

### `frontend/vue-app/src/components/__tests__/OptionsTable.spec.js`
- Add test cases:
  - **Renders annualized ROI column header** — assert `Annualized ROI` header is present
  - **Renders formatted ROI value for put options** — provide mock data with `annualizedRoi: 0.1234`, assert cell shows `12.34%`
  - **Renders fallback when annualizedRoi is null/undefined** — assert cell shows `—`
  - **Does not show ROI for call options (if applicable)** — if the table differentiates puts/calls, assert call rows show `—`

### `frontend/vue-app/src/tests/e2e/poll-market-data.spec.js` *(optional but recommended)*
- Add an assertion that the options chain table contains an `Annualized ROI` column header when put options are present in the response.

---

## Implementation Steps

1. **Inspect current `OptionsTable.vue`** to understand the existing column structure, how rows are rendered (v-for), and what data shape is passed as props.
2. **Determine the value format** of `annualizedRoi` from the backend (decimal fraction like `0.1234` vs already-multiplied percentage like `12.34`). Check `backend/api/routers/options_chain.py` or `backend/models/options_data.py` to confirm.
3. **Add the column header** `<th>Annualized ROI</th>` in the appropriate position in the `<thead>` row.
4. **Add the data cell** in the `<tbody>` row template:
   ```html
   <td>{{ formatRoi(option.annualizedRoi) }}</td>
   ```
5. **Add a `formatRoi` method** (or computed helper) in the component's `<script>` section:
   ```js
   formatRoi(value) {
     if (value == null) return '—';
     return (value * 100).toFixed(2) + '%';
   }
   ```
   *(Adjust multiplication factor based on confirmed backend format.)*
6. **Update unit tests** in `OptionsTable.spec.js` with the scenarios listed above.
7. **Run tests locally** to confirm all pass:
   ```bash
   cd frontend/vue-app && npm run test:unit
   ```
8. **Verify visually** (or via e2e) that the column appears correctly in the rendered table.

---

## Test Strategy

### Unit Tests (`OptionsTable.spec.js`)
- Column header renders with text `Annualized ROI`
- Cell renders `12.34%` when `annualizedRoi` is `0.1234`
- Cell renders `0.00%` when `annualizedRoi` is `0`
- Cell renders `—` when `annualizedRoi` is `null`
- Cell renders `—` when `annualizedRoi` is `undefined` (field absent)

### E2E Tests (`poll-market-data.spec.js`)
- Table contains `Annualized ROI` column header when options data is loaded

---

## Edge Cases to Handle

- `annualizedRoi` is `null` or `undefined` (call options, or backend didn't compute it)
- `annualizedRoi` is `0` — should display `0.00%`, not `—`
- `annualizedRoi` is negative (deep ITM puts) — display as-is, e.g. `-2.50%`
- Very large values — no special handling needed, just display
- Backend returns value as already-multiplied percentage vs decimal fraction — must confirm and handle correctly
