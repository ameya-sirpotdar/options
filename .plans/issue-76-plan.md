# Implementation Plan: Fix Calculate Trades Button Permanently Disabled

## Approach

The root cause is simple: `App.vue` renders `<InputPanel>` without passing the `:hasOptions` prop. Since `InputPanel.vue` defaults `hasOptions` to `false`, the `isCalcDisabled` computed property always returns `true`, keeping the button permanently disabled.

The fix is a one-line change in `App.vue` plus test coverage updates.

---

## Files to Modify

### 1. `frontend/vue-app/src/App.vue`
- **Change:** Add `:hasOptions="options.length > 0"` to the `<InputPanel>` component usage.
- The `options` ref is already available from `useMarketData()` destructuring at line 64, so no additional imports or composable changes are needed.

**Before (approximate):**
```vue
<InputPanel
  :ticker="ticker"
  :isLoading="isLoading"
  @submit="handleSubmit"
/>
```

**After:**
```vue
<InputPanel
  :ticker="ticker"
  :isLoading="isLoading"
  :hasOptions="options.length > 0"
  @submit="handleSubmit"
/>
```

### 2. `frontend/vue-app/src/components/__tests__/InputPanel.spec.js`
- **Change:** Add/update test cases to verify:
  - Button is **disabled** when `hasOptions` is `false` (default)
  - Button is **enabled** when `hasOptions` is `true` (and other required props are valid)
  - Ensure existing tests still pass

---

## Implementation Steps

1. Open `frontend/vue-app/src/App.vue`
2. Locate the `<InputPanel>` component usage (lines 9–21 per issue)
3. Add `:hasOptions="options.length > 0"` as a prop binding
4. Verify `options` is already destructured from `useMarketData()` — if not, add it
5. Open `frontend/vue-app/src/components/__tests__/InputPanel.spec.js`
6. Add test: mount InputPanel with `hasOptions: false` → assert Calculate Trades button has `disabled` attribute
7. Add test: mount InputPanel with `hasOptions: true` (and valid ticker/not loading) → assert Calculate Trades button does NOT have `disabled` attribute
8. Run `npm run test` (or vitest) to confirm all tests pass

---

## Test Strategy

### Unit Tests (`InputPanel.spec.js`)
- **Test 1:** `hasOptions=false` → button disabled
  - Mount `InputPanel` with `hasOptions: false`
  - Assert `[data-testid="calc-button"]` (or equivalent selector) has `disabled` attribute
- **Test 2:** `hasOptions=true` → button enabled
  - Mount `InputPanel` with `hasOptions: true`, valid ticker, `isLoading: false`
  - Assert button does NOT have `disabled` attribute
- **Test 3:** `hasOptions=true` but `isLoading=true` → button still disabled (if that's part of `isCalcDisabled` logic)
- **Test 4:** Regression — existing tests should continue to pass

### Integration / E2E
- Review `frontend/vue-app/src/tests/e2e/poll-market-data.spec.js` to see if it covers the button state after data loads; add assertion if missing.

---

## Edge Cases

- `options` could be `null` or `undefined` rather than an empty array — use `(options?.length ?? 0) > 0` or ensure `useMarketData` always initializes `options` as `[]`
- Button should remain disabled if `isLoading` is true even when options exist (verify existing `isCalcDisabled` logic handles this)
- If `options` is a reactive ref (not a plain array), ensure `.value` is not needed in the template (Vue 3 auto-unwraps refs in templates)

---

## Risks

- Low risk overall — single prop binding change
- Need to confirm the exact selector/ref name used in `InputPanel.spec.js` for the Calculate Trades button to write accurate tests
- Need to confirm `options` is destructured as a ref from `useMarketData()` and not renamed