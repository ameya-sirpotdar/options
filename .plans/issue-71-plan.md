# Implementation Plan — Issue #71: UI Improvements

## Approach Overview

The issue targets the frontend Vue app's `InputPanel.vue` component and overall layout width. We will:
1. Replace the ticker text input with a multi-select dropdown using checkboxes, defaulting to all 10 specified tickers selected.
2. Set the Delta default value to `0.30`.
3. Arrange the four controls (Tickers, Delta, Exp Date, VIX) in a compact multi-column layout rather than full-width rows.
4. Widen the main working area via CSS.
5. Update unit tests to reflect the new component structure.

---

## Files to Modify

### `frontend/vue-app/src/components/InputPanel.vue`
- **Ticker input → Multi-select dropdown with checkboxes**
  - Define a `DEFAULT_TICKERS` constant: `['QQQ', 'SPY', 'MSFT', 'AAPL', 'GOOG', 'META', 'NFLX', 'TSLA', 'NVDA', 'AMZN']`
  - Replace existing ticker `<input>` with a custom dropdown component (or a `<div>`-based toggle panel) that shows a button displaying selected tickers count/list, and a dropdown panel with a checkbox per ticker.
  - Use `v-model` / reactive array `selectedTickers` initialized to all 10 defaults.
  - Emit the selected tickers array to the parent on change (same event interface as before, just now an array).
  - Add a "Select All" / "Clear" convenience control inside the dropdown.
- **Delta default**
  - Change the default value of the `delta` data property / prop from whatever it currently is to `0.30`.
- **Layout**
  - Change the form layout from stacked full-width rows to a CSS grid or flexbox row, placing all four controls side-by-side (or 2×2 grid on smaller screens).
  - Each control should only occupy the width it needs, not the full row.

### `frontend/vue-app/src/assets/main.css` (or equivalent global styles)
- Increase the max-width of the main working area container (e.g., from `max-width: 960px` or similar to `max-width: 1400px` or `100%` with appropriate padding).
- Ensure the layout remains responsive.

### `frontend/vue-app/src/App.vue`
- If the container width constraint is defined here (e.g., a wrapper `<div>` with inline style or a class), update it to be wider.
- Verify that the ticker value passed to the API call is adapted to handle an array of tickers (join as comma-separated string or pass as array depending on backend contract).

### `frontend/vue-app/src/components/__tests__/InputPanel.spec.js`
- Update tests to reflect:
  - Ticker input is now a dropdown/checkbox group, not a plain text input.
  - Default selected tickers are the 10 specified ones.
  - Delta default is `0.30`.
  - Emitted value for tickers is an array (or joined string, matching implementation).
  - Dropdown opens/closes on button click.
  - Selecting/deselecting a ticker updates the emitted value.

### `frontend/vue-app/src/tests/e2e/poll-market-data.spec.js`
- Update any e2e selectors that target the old ticker text input to use the new dropdown.
- Verify the default state has all 10 tickers selected.

---

## Implementation Steps

1. **Audit current `InputPanel.vue`**
   - Identify current ticker input type, delta default value, and layout structure.
   - Note how values are emitted to parent / sent to API.

2. **Implement ticker multi-select dropdown**
   - Add `DEFAULT_TICKERS` constant array.
   - Add reactive `selectedTickers` ref initialized to `[...DEFAULT_TICKERS]`.
   - Build dropdown UI: a toggle button showing e.g. `"10 tickers selected"` or a comma-joined short list.
   - Dropdown panel: checkbox list rendered with `v-for` over `DEFAULT_TICKERS`.
   - Add "Select All" and "Clear" buttons.
   - Close dropdown on outside click (use `v-click-outside` directive or a document event listener).
   - Emit `selectedTickers` (as array or joined string) on change.

3. **Update Delta default**
   - Find the delta data property/prop and set its default to `0.30`.

4. **Refactor layout to multi-column**
   - Wrap the four controls in a CSS grid container: `display: grid; grid-template-columns: repeat(4, auto); gap: 1rem; align-items: end;`
   - On mobile (< 768px), collapse to 2 columns or stacked.

5. **Widen working area**
   - In `main.css` or `App.vue`, update the main container's `max-width` to `1400px` or `90vw`.

6. **Adapt API call for array tickers**
   - Ensure wherever `InputPanel` emits tickers, the parent/composable correctly formats the array for the backend (e.g., `tickers.join(',')` if the backend expects a comma-separated string).

7. **Update unit tests** in `InputPanel.spec.js`.

8. **Update e2e tests** in `poll-market-data.spec.js`.

9. **Manual smoke test**: verify all four controls render correctly, the dropdown opens/closes, tickers are sent correctly to the API, and the wider layout looks good.

---

## Edge Cases to Handle

- **Dropdown closes on outside click** — prevent accidental dismissal when clicking inside the panel.
- **No tickers selected** — disable the submit/run button and show a validation message.
- **Ticker array → API format** — confirm whether the backend expects a comma-separated string or an array; adapt accordingly without breaking existing functionality.
- **Responsive layout** — ensure the 4-column grid degrades gracefully on narrow screens.
- **Delta input validation** — ensure `0.30` default doesn't break any existing min/max validation.
- **Accessibility** — checkboxes should have proper `<label>` associations; dropdown should be keyboard-navigable.

---

## Test Strategy

### Unit Tests (`InputPanel.spec.js`)
- Renders a dropdown button for tickers (not a plain text input).
- All 10 default tickers are checked by default.
- Clicking the button opens the dropdown panel.
- Unchecking a ticker removes it from the emitted value.
- "Clear" button deselects all; "Select All" re-selects all.
- Delta field has default value `0.30`.
- Submit with 0 tickers selected is disabled or shows error.

### E2E Tests (`poll-market-data.spec.js`)
- Page loads with dropdown showing all 10 tickers selected.
- User can open dropdown, deselect a ticker, and submit — API call reflects updated ticker list.
- Working area is visibly wider than before (can assert container width > threshold).
