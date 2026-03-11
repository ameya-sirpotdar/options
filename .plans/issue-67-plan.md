# Revised Implementation Plan: Fix Tickers Binding and Prop Wiring

## Root Cause Summary

The bug originates in `App.vue`, not in `useMarketData.js`. Inside Vue templates, refs are auto-unwrapped, so writing `tickers.value = $event` attempts to set a `.value` property on a raw string primitive, throwing:

```
TypeError: Cannot create property 'value' on string ''
```

Additionally, `App.vue` passes a single `:loading` prop to `InputPanel`, but `InputPanel` expects two separate props (`:isPolling` and `:isCalculating`), meaning loading and disabled states never activate. Unit tests for `InputPanel` and `useMarketData` are also stale and must be updated to reflect the current API surface.

**`useMarketData.js` and `InputPanel.vue` are correct and must not be modified.**

---

## Files to Modify

| File | Change Summary |
|---|---|
| `frontend/vue-app/src/App.vue` | Fix `tickers.value` → `tickers`; fix prop wiring to `InputPanel` |
| `frontend/vue-app/src/tests/InputPanel.spec.js` | Update stale test expectations |
| `frontend/vue-app/src/tests/useMarketData.spec.js` | Update stale imports and API surface references |

## Files NOT to Modify

| File | Reason |
|---|---|
| `useMarketData.js` | `ref('')` initialization is correct; changing it would break comma-split downstream logic |
| `InputPanel.vue` | Component is correct; it only needs proper prop wiring from `App.vue` |

---

## Step 1 — Fix `App.vue`: Tickers Binding

**File:** `frontend/vue-app/src/App.vue`, line 15

The template must use the auto-unwrapped ref name directly, matching the correct pattern already used for `delta` and `expiry`.

```diff
- @update:tickers="tickers.value = $event"
+ @update:tickers="tickers = $event"
```

**Why:** In Vue 3 templates, `setup()`-returned refs are automatically unwrapped. `tickers` already resolves to the raw string value inside the template. Assigning to `tickers` (not `tickers.value`) correctly triggers Vue's reactivity setter. Writing `.value` on a string primitive throws a `TypeError`.

---

## Step 2 — Fix `App.vue`: Prop Wiring to `InputPanel`

**File:** `frontend/vue-app/src/App.vue`

`InputPanel` declares two distinct boolean props — `:isPolling` and `:isCalculating` — but `App.vue` currently passes a single combined `:loading` prop that `InputPanel` does not recognize. Replace the incorrect prop with the two props `InputPanel` actually expects.

```diff
  <InputPanel
    :tickers="tickers"
    :delta="delta"
    :expiry="expiry"
-   :loading="loading"
+   :isPolling="isPolling"
+   :isCalculating="isCalculating"
    @update:tickers="tickers = $event"
    @update:delta="delta = $event"
    @update:expiry="expiry = $event"
  />
```

Ensure `isPolling` and `isCalculating` are the reactive state variables exposed from `useMarketData` in the `setup` block. If the composable returns these under different names, align the binding to match the composable's actual return values — do not rename anything inside `useMarketData.js`.

---

## Step 3 — Update `InputPanel.spec.js`

**File:** `frontend/vue-app/src/tests/InputPanel.spec.js`

The existing tests reference outdated expectations. Apply the following categories of fixes:

### 3a — Update prop names in test mounts

```diff
  const wrapper = mount(InputPanel, {
    props: {
-     loading: true,
+     isPolling: false,
+     isCalculating: true,
    },
  })
```

### 3b — Update button text assertions

Replace any stale button label strings with the text currently rendered by `InputPanel.vue`. Inspect the component's template for the exact strings before updating.

```diff
- expect(wrapper.find('button').text()).toBe('Fetch')
+ expect(wrapper.find('button').text()).toBe('<current label from InputPanel.vue>')
```

### 3c — Update disabled-state assertions

Verify that the button disabled logic now activates correctly via `isPolling` / `isCalculating` props:

```diff
- const wrapper = mount(InputPanel, { props: { loading: true } })
+ const wrapper = mount(InputPanel, { props: { isPolling: true, isCalculating: false } })
  expect(wrapper.find('button').attributes('disabled')).toBeDefined()
```

---

## Step 4 — Update `useMarketData.spec.js`

**File:** `frontend/vue-app/src/tests/useMarketData.spec.js`

The existing tests use stale import names and reference an outdated API surface. Apply the following fixes:

### 4a — Correct import names

```diff
- import { useMarketData } from '../composables/marketData'
+ import { useMarketData } from '../composables/useMarketData'
```

Adjust the import path to match the actual filename exactly.

### 4b — Correct returned property names

Update any destructured return values to match what `useMarketData` currently returns. Do not rename properties inside the composable itself.

```diff
- const { data, loading, fetchData } = useMarketData()
+ const { <actual return names from useMarketData.js> } = useMarketData()
```

### 4c — Correct `tickers` type assertions

The composable initializes `tickers` as `ref('')`. Any test asserting it is an object or has a different initial value must be corrected:

```diff
- expect(tickers.value).toEqual({})
+ expect(tickers.value).toBe('')
```

---

## Verification Checklist

After applying all changes, confirm the following before marking the work complete:

- [ ] `tickers` binding in `App.vue` template uses `tickers = $event` (no `.value`)
- [ ] `InputPanel` receives `:isPolling` and `:isCalculating` from `App.vue`; `:loading` prop is removed
- [ ] `useMarketData.js` is unchanged
- [ ] `InputPanel.vue` is unchanged
- [ ] `InputPanel.spec.js` passes with correct prop names and button text
- [ ] `useMarketData.spec.js` passes with correct import path and API surface
- [ ] No `TypeError: Cannot create property 'value' on string ''` in browser console
- [ ] Loading and disabled states on `InputPanel` activate correctly during polling and calculation