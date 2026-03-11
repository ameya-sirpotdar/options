# Implementation Plan: Fix Frontend Polling Data Error (Issue #67)

## Approach Overview

The error `TypeError: Cannot create property 'value' on string ''` originates in `App.vue`, not in `useMarketData.js`. In Vue templates, refs are auto-unwrapped — `tickers` inside a template expression already resolves to the raw string value, not the ref object. Writing `tickers.value = $event` therefore attempts to set a `.value` property on a string primitive, which throws the TypeError.

The fix is a one-character change in `App.vue`, plus correcting a prop-name mismatch in the same file and updating two stale test files to match the current API surface.

**Do not modify `useMarketData.js` or `InputPanel.vue`** — the composable's `ref('')` initialization is correct, and the component itself is fine.

---

## Root Cause Analysis

In `App.vue`, the event binding for `tickers` reads:

```js
@update:tickers="tickers.value = $event"   // ← BUG
```

Vue's template compiler auto-unwraps refs in template scope, so `tickers` is already the raw string `''`. Assigning `.value` onto a string primitive is illegal and throws:

```
TypeError: Cannot create property 'value' on string ''
```

The adjacent bindings show the correct pattern:

```js
@update:delta="delta = $event"       // ✓ correct
@update:expiry="expiry = $event"     // ✓ correct
@update:tickers="tickers.value = $event"  // ✗ bug — spurious .value
```

A secondary bug exists on the same file: `App.vue` passes `:loading="loading"` to `InputPanel`, but `InputPanel` expects two separate props — `:isPolling` and `:isCalculating`. Because the prop names never match, the loading and disabled states inside `InputPanel` never activate.

---

## Files to Modify

### 1. `frontend/vue-app/src/App.vue`

**Primary fix — remove spurious `.value`:**

```diff
- @update:tickers="tickers.value = $event"
+ @update:tickers="tickers = $event"
```

**Secondary fix — correct prop wiring to InputPanel:**

```diff
- <InputPanel
-   :loading="loading"
-   ...
- />
+ <InputPanel
+   :isPolling="isPolling"
+   :isCalculating="isCalculating"
+   ...
+ />
```

Ensure `isPolling` and `isCalculating` are the reactive values already maintained in the component's setup (or `data`). If the current code only tracks a single `loading` boolean, split it into two appropriately named refs that map to what `InputPanel` expects.

### 2. `frontend/vue-app/src/components/__tests__/InputPanel.spec.js`

Update stale test expectations to match the current component API:

- Correct any outdated button-text assertions (e.g. old label vs. current label)
- Correct prop names passed in test mounts — replace any use of `loading` with `isPolling` / `isCalculating` as appropriate
- Remove or update any assertions that relied on the broken prop wiring

### 3. `frontend/vue-app/src/composables/__tests__/useMarketData.spec.js`

Update stale imports and API surface references:

- Fix any import paths or named exports that no longer match the current composable
- Update function/ref names in test calls to match what `useMarketData.js` currently exports
- Ensure tests do **not** assert that `tickers` initializes as anything other than a string (the `ref('')` initialization is correct and intentional)

---

## Files NOT to Modify

| File | Reason |
|---|---|
| `frontend/vue-app/src/composables/useMarketData.js` | `ref('')` is correct; the bug is in the template, not the composable. Changing it to `ref(null)` or `ref({})` would break downstream code that splits the string on commas. |
| `frontend/vue-app/src/components/InputPanel.vue` | The component itself is correct. It only needs accurate prop values passed from `App.vue`. |

---

## Implementation Steps

### Step 1: Fix the template binding in `App.vue`

Open `App.vue` and locate line 15 (or wherever the `@update:tickers` binding appears):

```diff
- @update:tickers="tickers.value = $event"
+ @update:tickers="tickers = $event"
```

This is the primary bug fix. The change is minimal and surgical — no other logic needs to change.

### Step 2: Fix prop wiring in `App.vue`

In the same file, find the `<InputPanel>` usage and correct the loading-state props:

```diff
  <InputPanel
-   :loading="loading"
+   :isPolling="isPolling"
+   :isCalculating="isCalculating"
    :tickers="tickers"
    :expiry="expiry"
    :delta="delta"
    @update:tickers="tickers = $event"
    @update:expiry="expiry = $event"
    @update:delta="delta = $event"
  />
```

If `App.vue` currently only has a single `loading` ref, refactor it into `isPolling` and `isCalculating` refs and set them at the appropriate points in the poll and calculate workflows:

```js
// In setup() or <script setup>
const isPolling = ref(false)
const isCalculating = ref(false)

// When polling starts/ends
async function pollMarketData() {
  isPolling.value = true
  try {
    // ... existing poll logic
  } finally {
    isPolling.value = false
  }
}

// When calculation starts/ends
async function calculate() {
  isCalculating.value = true
  try {
    // ... existing calculate logic
  } finally {
    isCalculating.value = false
  }
}
```

### Step 3: Update `InputPanel.spec.js`

Review the current `InputPanel.vue` source to confirm the exact prop names and button text, then update the spec to match:

```js
// Example: mount with correct props
const wrapper = mount(InputPanel, {
  props: {
    tickers: '',
    expiry: '',
    delta: '',
    isPolling: false,      // was: loading: false
    isCalculating: false,  // add if missing
  }
})

// Example: update button-text assertions to match current labels
expect(wrapper.find('button[data-testid="poll-btn"]').text()).toBe('Poll Market Data')
```

Verify each test case passes with the corrected prop names before moving on.

### Step 4: Update `useMarketData.spec.js`

Audit the spec against the current composable exports:

```js
// Confirm the import matches what the file actually exports
import { useMarketData } from '../useMarketData'

// Confirm ref names match
const { tickers, poll, /* etc. */ } = useMarketData()

// Do NOT change the initialization assertion — ref('') is correct
expect(tickers.value).toBe('')  // ✓ this should remain as-is
```

Fix any broken import paths, renamed exports, or removed/added function signatures so the suite is green against the current codebase.

---

## Test Strategy

| Layer | File | What to verify |
|---|---|---|
| Unit — composable | `useMarketData.spec.js` | Correct exports and API surface; `tickers` initializes as `''` |
| Unit — component | `InputPanel.spec.js` | Component renders correctly with `isPolling`/`isCalculating` props; button states activate as expected |
| Manual / existing e2e | — | Enter ticker `QQQ`, expiration `2026-03-26`, click Poll Market Data — confirm no `TypeError` in console |

No new test files need to be created as part of this fix. The existing unit test files need only to be brought up to date with the current API surface.

---

## Edge Cases Confirmed Unaffected by This Fix

1. **Comma-separated tickers** — `tickers` remains `ref('')`; splitting on commas in the composable continues to work correctly.
2. **Rapid poll clicks** — unrelated to this bug; existing debounce/disable logic is unaffected.
3. **Backend unavailable** — the TypeError was thrown before any network call; removing it allows the error-handling path to work as designed.
4. **Empty string initial state** — template guards that check `v-if="tickers"` behave identically before and after the fix since the ref type does not change.