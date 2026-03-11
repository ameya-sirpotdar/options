# Implementation Plan: Fix Frontend Polling Data Error (Issue #67)

## Approach Overview

The error `TypeError: Cannot create property 'value' on string ''` occurs in the `onUpdate` handler for `tickers`. This strongly suggests that somewhere in the Vue app, a reactive ref or store property for `tickers` is initialized as an empty string `''` instead of an object or `null`. When the polling response arrives and the code tries to assign `tickers.value = <someObject>`, Vue (or the store) cannot set `.value` on a primitive string.

The fix is to:
1. Locate the `tickers` initialization in `useMarketData.js` (or related composable/store)
2. Change the initial value from `''` to `null` or `{}` as appropriate
3. Update any template/component guards to handle `null` gracefully
4. Add a Playwright e2e test covering the Poll Market Data flow

## Root Cause Analysis

From the stack trace:
```
at Ce.onUpdate:tickers.N.<computed>.N.<computed>
```
This points to a Valtio/Vue reactive store or a `ref('')` initialization. In `useMarketData.js`, the `tickers` ref is likely declared as:
```js
const tickers = ref('')  // ← WRONG: should be ref(null) or ref({})
```
When the API response comes back and the composable tries to set structured data on it, the assignment fails because you cannot add properties to a primitive string.

## Files to Modify

### 1. `frontend/vue-app/src/composables/useMarketData.js`
- Find the `tickers` ref initialization
- Change `ref('')` → `ref(null)` (or `ref({})` if the template expects an object)
- Ensure the `onUpdate` handler properly assigns the full response object
- Add null-safety guards where `tickers.value` is accessed

### 2. `frontend/vue-app/src/components/InputPanel.vue`
- Review any `v-model` or binding tied to `tickers` — ensure it handles `null` gracefully
- Add `v-if` guards if needed

### 3. `frontend/vue-app/src/composables/__tests__/useMarketData.spec.js`
- Add unit test covering the case where polling returns structured data (not a string)
- Verify `tickers.value` is set correctly after a successful poll

## Files to Create

### 1. `frontend/vue-app/tests/e2e/poll-market-data.spec.js`
Playwright e2e test that:
- Navigates to the app URL
- Enters ticker `QQQ` and expiration date `2026-03-26`
- Clicks "Poll Market Data"
- Asserts no JS errors occur
- Asserts a loading state appears
- Asserts results/data are displayed (or a meaningful error message if backend is unavailable)

### 2. `frontend/vue-app/playwright.config.js` (if not already present)
- Configure Playwright with base URL, browser targets, and test directory

## Implementation Steps

### Step 1: Diagnose and fix `useMarketData.js`

```js
// BEFORE (likely current code)
const tickers = ref('')

// AFTER
const tickers = ref(null)
```

Also check the `onUpdate` / poll response handler:
```js
// Ensure the assignment is to the ref's .value, not the ref itself
tickers.value = response.data  // correct
// NOT: tickers = response.data  (would replace the ref)
```

And add null guards in computed properties or template expressions:
```js
// In composable
const tickerData = computed(() => tickers.value ?? {})
```

### Step 2: Update InputPanel.vue if needed

If `InputPanel.vue` has a `v-model` bound to `tickers` or reads from it:
```html
<!-- Add null guard -->
<div v-if="tickers">...</div>
```

### Step 3: Update unit tests in `useMarketData.spec.js`

Add test case:
```js
it('should set tickers to response data after successful poll', async () => {
  // mock API response
  // call poll function
  // assert tickers.value equals expected object, not a string
  expect(typeof tickers.value).not.toBe('string')
})
```

### Step 4: Add Playwright configuration

```js
// playwright.config.js
import { defineConfig } from '@playwright/test'
export default defineConfig({
  testDir: './tests/e2e',
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:5173',
  },
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:5173',
    reuseExistingServer: !process.env.CI,
  },
})
```

### Step 5: Write Playwright e2e test

```js
// tests/e2e/poll-market-data.spec.js
import { test, expect } from '@playwright/test'

test.describe('Poll Market Data', () => {
  test('should not throw JS error when polling with valid inputs', async ({ page }) => {
    const jsErrors = []
    page.on('pageerror', err => jsErrors.push(err.message))

    await page.goto('/')
    
    // Fill in ticker
    await page.getByLabel(/ticker/i).fill('QQQ')
    
    // Fill in expiration date
    await page.getByLabel(/exp.*date/i).fill('2026-03-26')
    
    // Click Poll Market Data
    await page.getByRole('button', { name: /poll market data/i }).click()
    
    // Wait briefly for any async errors to surface
    await page.waitForTimeout(1000)
    
    // Assert no JS errors
    expect(jsErrors.filter(e => e.includes('Cannot create property'))).toHaveLength(0)
    
    // Assert loading or result state appears (not stuck)
    // Either a loading indicator or results table should be visible
    const hasLoading = await page.locator('[data-testid="loading"]').isVisible().catch(() => false)
    const hasResults = await page.locator('[data-testid="options-table"]').isVisible().catch(() => false)
    const hasError = await page.locator('[data-testid="error-message"]').isVisible().catch(() => false)
    
    expect(hasLoading || hasResults || hasError).toBe(true)
  })

  test('should display error gracefully when backend is unavailable', async ({ page }) => {
    const jsErrors = []
    page.on('pageerror', err => jsErrors.push(err.message))

    await page.goto('/')
    await page.getByLabel(/ticker/i).fill('QQQ')
    await page.getByLabel(/exp.*date/i).fill('2026-03-26')
    await page.getByRole('button', { name: /poll market data/i }).click()
    
    await page.waitForTimeout(2000)
    
    // No TypeError should occur regardless of backend availability
    const typeErrors = jsErrors.filter(e => e.includes('TypeError'))
    expect(typeErrors).toHaveLength(0)
  })
})
```

### Step 6: Add Playwright to package.json

```json
{
  "devDependencies": {
    "@playwright/test": "^1.40.0"
  },
  "scripts": {
    "test:e2e": "playwright test",
    "test:e2e:ui": "playwright test --ui"
  }
}
```

## Test Strategy

- **Unit tests** (`useMarketData.spec.js`): Verify tickers ref initializes as null/object, verify poll response correctly sets tickers.value
- **Component tests** (`InputPanel.spec.js`): Verify component renders without error when tickers is null
- **E2E tests** (Playwright): Verify full poll flow from UI input to response without JS errors

## Edge Cases to Handle

1. `tickers` is `null` initially — template must not crash on `tickers.someProperty`
2. API returns empty array `[]` — should render empty state, not error
3. API returns error — should show error message, not crash
4. User clicks Poll multiple times rapidly — debounce or disable button during loading
5. Expiration date format mismatch — validate before sending
